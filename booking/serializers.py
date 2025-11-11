from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Room, Reservation, Profile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["user", "phone", "email_address"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            "room_id",
            "room_name",
            "capacity",
            "location",
            "facilities",
            "room_type",
            "imagePath",
        ]


class ReservationSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)          # for reading
    user = UserSerializer(read_only=True)
    room_id = serializers.PrimaryKeyRelatedField(  # for creating/updating
        queryset=Room.objects.all(),
        source="room",
        write_only=True
    )

    class Meta:
        model = Reservation
        fields = [
            "booking_id",
            "room",
            "room_id",
            "user",
            "start_time",
            "end_time",
            "date",
            "status",
            "created_at",
        ]
        read_only_fields = ["booking_id", "user", "status", "created_at"]

    def create(self, validated_data):
        # Get user from request (JWT auth)
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["user"] = request.user

        # Default booking status (you’re currently using Confirmed)
        validated_data.setdefault("status", "Confirmed")

        return super().create(validated_data)
