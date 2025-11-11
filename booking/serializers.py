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
  room_name = serializers.CharField(source="room.room_name", read_only=True)

  class Meta:
      model = Reservation
      fields = [
          "booking_id",
          "room",
          "room_name",
          "date",
          "start_time",
          "end_time",
          "status",
      ]
      read_only_fields = ["booking_id", "user"]
