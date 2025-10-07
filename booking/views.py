from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReservationForm
from .models import Room, Reservation, Profile
from .forms import SignUpForm
from .utils import send_booking_email


# index (homepage)

def index(request):
    return render(request, "booking/index.html")


# signup (create profile)
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # automatically log the user in after signup
            return redirect("index")
    else:
        form = SignUpForm()
    return render(request, "booking/signup.html", {"form": form})

# login
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "booking/login.html")


# logout
def logout_view(request):
    logout(request)
    return redirect("index")


# list all rooms
def available_rooms(request):
    rooms = Room.objects.all()
    return render(request, "booking/rooms.html", {"rooms": rooms})

# manage bookings (only user’s bookings)
@login_required(login_url="login")
def manage_bookings(request):
    user_reservations = Reservation.objects.filter(user=request.user).order_by("date", "start_time")
    return render(request, "booking/manage_bookings.html", {"reservations": user_reservations})

@login_required
def edit_booking(request, booking_id):
    reservation = get_object_or_404(Reservation, pk=booking_id, user=request.user)
    if request.method == "POST":
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, "Reservation updated successfully!")
            return redirect("manage_bookings")
    else:
        form = ReservationForm(instance=reservation)
    return render(request, "booking/edit_booking.html", {"form": form})

@login_required
def cancel_booking(request, booking_id):
    reservation = get_object_or_404(Reservation, pk=booking_id, user=request.user)
    reservation.status = "Cancelled"
    reservation.save()

    # Email user
    subject = "Your Reservation Cancelled"
    context = {
        "user": request.user,
        "room": reservation.room,
        "date": reservation.date,
        "start_time": reservation.start_time,
        "end_time": reservation.end_time,
    }
    send_booking_email(request.user.email, subject, "reservation_cancellation", context)

    messages.success(request, "Reservation cancelled and notification email sent.")
    return redirect("cancellation_success")



@login_required
def make_reservation(request):
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.status = "Confirmed"
            reservation.save()

            # Send notification email
            subject = "Your Reservation Confirmation"
            context = {
                "user": request.user,
                "room": reservation.room,
                "date": reservation.date,
                "start_time": reservation.start_time,
                "end_time": reservation.end_time,
            }
            send_booking_email(request.user.email, subject, "reservation_confirmation", context)

            messages.success(request, "Reservation made and email sent.")
            return redirect("reservation_success")
    else:
        form = ReservationForm()

    return render(request, "booking/make_reservation.html", {"form": form})




def reservation_success(request):
    return render(request, "booking/reservation_success.html")

def cancellation_success(request):
    return render(request, "booking/cancellation_success.html")