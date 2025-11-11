from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth.models import User

from .models import Room, Reservation
from .serializers import RoomSerializer, UserSerializer, ReservationSerializer
from .utils import send_booking_email



class RoomViewSet(viewsets.ModelViewSet):
    """
    /api/rooms/
    - GET (anyone): list rooms
    - GET /api/rooms/{id}/ (anyone): view a room
    - POST/PUT/PATCH/DELETE: admin only
    """
    queryset = Room.objects.all().order_by("room_name")
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class RegisterView(APIView):
    """
    /api/register/  [POST]
    Simple user registration for React.

    Expected JSON body:
    {
        "username": "yourname",
        "password1": "Password123!",
        "password2": "Password123!",
        "email": "optional@email.com"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password1 = request.data.get("password1") or ""
        password2 = request.data.get("password2") or ""
        email = (request.data.get("email") or "").strip()

        errors = {}

        # Username checks
        if not username:
            errors.setdefault("username", []).append("This field is required.")
        elif User.objects.filter(username=username).exists():
            errors.setdefault("username", []).append("A user with that username already exists.")

        # Password checks
        if not password1:
            errors.setdefault("password1", []).append("This field is required.")
        if not password2:
            errors.setdefault("password2", []).append("This field is required.")
        if password1 and password2 and password1 != password2:
            errors.setdefault("password2", []).append("Passwords do not match.")
        if password1 and len(password1) < 8:
            errors.setdefault("password1", []).append("Password must be at least 8 characters long.")

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password1,
            email=email or ""
        )

        data = UserSerializer(user).data
        return Response(data, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    """
    GET /api/me/
    Returns the logged-in user's data (used by React navbar).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class ReservationViewSet(viewsets.ModelViewSet):
    """
    API for reservations.

    - Auth required.
    - Normal user:
        * list: only their reservations
        * create: creates their own, status=Confirmed + confirmation email
        * update: only their own; can edit details; can set status=Cancelled (triggers email)
    - Admin (is_staff):
        * full access to all reservations
    """
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return (
                Reservation.objects
                .select_related("room", "user")
                .order_by("date", "start_time")
            )
        return (
            Reservation.objects
            .select_related("room")
            .filter(user=user)
            .order_by("date", "start_time")
        )

    def perform_create(self, serializer):
        """
        Called when React does POST /api/reservations/.
        Creates reservation for current user, sets Confirmed, sends confirmation email.
        """
        user = self.request.user

        # Normal users create for themselves.
        # (If you later want admin to create for others, you can extend this.)
        reservation = serializer.save(user=user, status="Confirmed")

        # Send confirmation email
        subject = "Your Reservation Confirmation"
        context = {
            "user": reservation.user,
            "room": reservation.room,
            "date": reservation.date,
            "start_time": reservation.start_time,
            "end_time": reservation.end_time,
        }
        send_booking_email(
            reservation.user.email,
            subject,
            "reservation_confirmation",
            context,
        )

    def perform_update(self, serializer):
        """
        Called on PATCH / PUT /api/reservations/<id>/.
        - User can only edit their own.
        - User can only cancel (set status=Cancelled) their own.
        - Admin can change anything.
        """
        user = self.request.user
        reservation = self.get_object()
        old_status = reservation.status  # track for cancellation email

        # Permission: only owner or admin
        if not user.is_staff and reservation.user != user:
            raise PermissionDenied("You cannot modify this reservation.")

        # Lock down fields for non-admins
        if not user.is_staff:
            # Can't change owner
            serializer.validated_data.pop("user", None)

            # If they try to change status to something other than Cancelled, ignore it
            if "status" in serializer.validated_data:
                new_status = serializer.validated_data["status"]
                if new_status != "Cancelled":
                    serializer.validated_data.pop("status", None)

        # Save changes
        reservation = serializer.save()

        # If status changed from something else to Cancelled -> send cancellation email
        if old_status != "Cancelled" and reservation.status == "Cancelled":
            subject = "Your Reservation Cancelled"
            context = {
                "user": reservation.user,
                "room": reservation.room,
                "date": reservation.date,
                "start_time": reservation.start_time,
                "end_time": reservation.end_time,
            }
            send_booking_email(
                reservation.user.email,
                subject,
                "reservation_cancellation",
                context,
            )

    def destroy(self, request, *args, **kwargs):
        """
        For safety, normal users shouldn't hard-delete; they cancel instead.
        Admins can delete.
        """
        user = request.user
        reservation = self.get_object()

        if not user.is_staff and reservation.user != user:
            return Response(
                {"detail": "You cannot delete this reservation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def my(self, request):
        """
        Optional: GET /api/reservations/my/ to fetch only current user's reservations.
        """
        qs = (
            Reservation.objects
            .select_related("room")
            .filter(user=request.user)
            .order_by("date", "start_time")
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
