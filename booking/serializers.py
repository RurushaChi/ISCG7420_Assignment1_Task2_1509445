from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Room, Reservation, Profile
from datetime import date

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
            "react_image_paths",
        ]


class ReservationSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source="room.room_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "booking_id",
            "room",
            "room_name",
            "user",
            "username",
            "date",
            "start_time",
            "end_time",
            "status",
        ]
        read_only_fields = ["booking_id"]

        def validate_date(self, value):
            if value < date.today():
                raise serializers.ValidationError(
                    "Reservation date cannot be in the past."
                )
            return value


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(source="profile.phone", required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "password", "phone"]

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        user.set_password(password or User.objects.make_random_password())
        user.save()
        # create/update profile.phone if provided
        if profile_data and "phone" in profile_data:
            Profile.objects.update_or_create(user=user, defaults={"phone": profile_data.get("phone", "")})
        else:
            Profile.objects.get_or_create(user=user)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        if profile_data:
            Profile.objects.update_or_create(user=instance, defaults={"phone": profile_data.get("phone", "")})
        return instance
