from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from booking.models import Reservation
from datetime import timedelta

class Command(BaseCommand):
    help = "Send reminder emails for tomorrow's reservations."

    def handle(self, *args, **kwargs):
        tomorrow = timezone.localdate() + timedelta(days=1)
        reservations = Reservation.objects.filter(date=tomorrow, status="Confirmed")

        for reservation in reservations:
            send_mail(
                subject="Reminder: Your Room Reservation is Tomorrow",
                message=(
                    f"Hi {reservation.user.username},\n\n"
                    f"This is a friendly reminder that you have booked "
                    f"Room {reservation.room.room_name} on {reservation.date} "
                    f"from {reservation.start_time} to {reservation.end_time}.\n\n"
                    f"Thank you,\nConference Booking System"
                ),
                from_email="chiker03@myunitec.ac.nz",  # must match verified SendGrid sender
                recipient_list=[reservation.user.email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Reminder sent to {reservation.user.email}"))
