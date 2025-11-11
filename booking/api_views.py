from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Room, Reservation
from .serializers import (
    RoomSerializer,
    ReservationSerializer,
    UserSerializer,
)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all().order_by("room_name")
    serializer_class = RoomSerializer

    def get_permissions(self):
        # Anyone can view rooms; only staff can modify
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Reservation.objects.select_related("room", "user").order_by("date", "start_time")
        return Reservation.objects.select_related("room").filter(user=user).order_by("date", "start_time")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def perform_create(self, serializer):
        # Serializer already sets user from context; this ensures save() runs
        serializer.save()

    @action(detail=False, methods=["get"])
    def my(self, request):
        qs = Reservation.objects.select_related("room").filter(
            user=request.user
        ).order_by("date", "start_time")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
