from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

from django.contrib.auth.models import User

from .models import Room, Reservation
from .serializers import RoomSerializer, UserSerializer, ReservationSerializer, AdminUserSerializer
from .utils import send_booking_email


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all().order_by("room_name")
    serializer_class = RoomSerializer

    def get_permissions(self):
        # Public can view rooms; mutation is admin-only
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]



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
        user = self.request.user

        # Admin can optionally create for any user (by id)
        target_user = user
        if user.is_staff:
            user_id = self.request.data.get("user")
            if user_id:
                try:
                    target_user = User.objects.get(pk=user_id)
                except User.DoesNotExist:
                    raise PermissionDenied("Selected user does not exist.")

        reservation = serializer.save(user=target_user, status="Confirmed")

        # Email: confirmation
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
        user = self.request.user
        reservation = self.get_object()
        old_status = reservation.status

        # Only owner or admin
        if not user.is_staff and reservation.user != user:
            raise PermissionDenied("You cannot modify this reservation.")

        if not user.is_staff:
            # Can't change owner
            serializer.validated_data.pop("user", None)

            # Only allow status=Cancelled from user
            if "status" in serializer.validated_data:
                new_status = serializer.validated_data["status"]
                if new_status != "Cancelled":
                    serializer.validated_data.pop("status", None)

        # Admin: no extra restrictions
        reservation = serializer.save()

        # If now cancelled → send cancellation email
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
        qs = (
            Reservation.objects
            .select_related("room")
            .filter(user=request.user)
            .order_by("date", "start_time")
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def perform_destroy(self, instance):
        # Protect superusers and prevent deleting yourself
        if instance.is_superuser:
            raise PermissionDenied("Cannot delete a superuser.")
        if self.request.user == instance:
            raise PermissionDenied("You cannot delete your own account.")
        super().perform_destroy(instance)
