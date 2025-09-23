# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# Extend user info if needed
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    email_address = models.EmailField(blank=True)

    def __str__(self):
        return self.user.username


# Room model
class Room(models.Model):
    ROOM_TYPES = [
        ("Conference", "Conference"),
        ("Seminar", "Seminar"),
        ("Huddle", "Huddle"),
    ]

    room_id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=100, default="Default Room")
    capacity = models.PositiveIntegerField()
    location = models.CharField(max_length=255)
    facilities = models.TextField(blank=True)   # e.g., "Projector, Whiteboard"
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES)
    imagePath = models.CharField(max_length=255, blank=True, null=True)  # path or URL

    def __str__(self):
        return f"Room {self.room_id} - {self.location}"


# Booking model
class RoomBooking(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Cancelled", "Cancelled"),
    ]

    booking_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(start_time__lt=models.F("end_time")),
                                   name="check_start_before_end"),
        ]

    def clean(self):
        """Custom validation to prevent overlapping bookings."""
        overlapping = RoomBooking.objects.filter(
            room=self.room,
            date=self.date,
            status="Confirmed"
        ).exclude(booking_id=self.booking_id).filter(
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )

        if overlapping.exists():
            raise ValidationError("This room is already booked for the selected time range.")

    def __str__(self):
        return f"Booking {self.booking_id} - Room {self.room.room_id} by {self.user.username}"
