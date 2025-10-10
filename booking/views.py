from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReservationForm
from .models import Room, Reservation, Profile
from .forms import SignUpForm
from .utils import send_booking_email
from .models import Room
from django import forms
from .forms import AdminReservationForm


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

#Manage Booking (Admin and Users)
@login_required(login_url="login")
def manage_bookings(request):
    # 👇 Admins can see ALL reservations
    if request.user.is_staff:
        user_reservations = Reservation.objects.select_related("room", "user").order_by("date", "start_time")
    else:
        # 👇 Regular users only see their own
        user_reservations = Reservation.objects.filter(user=request.user).select_related("room").order_by("date", "start_time")

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
    if request.user.is_superuser:
        reservation = get_object_or_404(Reservation, pk=booking_id)
    else:
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

        # Hide user field dynamically for non-admins
        if not request.user.is_staff and "user" in form.fields:
            form.fields.pop("user")

        if form.is_valid():
            reservation = form.save(commit=False)

            # Admins can choose a user, regular users are auto-assigned
            if request.user.is_staff and "user" in form.cleaned_data:
                reservation.user = form.cleaned_data.get("user")
            else:
                reservation.user = request.user

            reservation.status = "Confirmed"
            reservation.save()

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
                reservation.user.email, subject, "reservation_confirmation", context
            )

            messages.success(request, "Reservation made and email sent.")
            return redirect("reservation_success")

    else:
        form = ReservationForm()
        # Hide user field in GET for non-admins
        if not request.user.is_staff and "user" in form.fields:
            form.fields.pop("user")

    return render(request, "booking/make_reservation.html", {"form": form})



def reservation_success(request):
    return render(request, "booking/reservation_success.html")

def cancellation_success(request):
    return render(request, "booking/cancellation_success.html")

#Admin functions only

@staff_member_required
def manage_users(request):
    users = User.objects.all()
    return render(request, "booking/manage_users.html", {"users": users})

@staff_member_required
def add_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User added successfully.")
            return redirect("manage_users")
    else:
        form = SignUpForm()
    return render(request, "booking/add_user.html", {"form": form})

@staff_member_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, "profile", None)

    if request.method == "POST":
        form = SignUpForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            updated_user.save()
            # Update profile phone number
            if profile:
                profile.phone = form.cleaned_data.get("phone")
                profile.save()
            messages.success(request, "User updated successfully.")
            return redirect("manage_users")
    else:
        # Prefill phone if it exists
        initial_data = {"phone": profile.phone if profile else ""}
        form = SignUpForm(instance=user, initial=initial_data)

    return render(request, "booking/edit_user.html", {"form": form, "user": user})

@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "You cannot delete another admin.")
    else:
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect("manage_users")


# --- Room Form ---
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["room_name", "capacity", "location", "facilities", "room_type", "imagePath"]


# --- Manage Rooms View ---
@staff_member_required
def manage_rooms(request):
    rooms = Room.objects.all()
    return render(request, "booking/manage_rooms.html", {"rooms": rooms})


@staff_member_required
def add_room(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Room added successfully.")
            return redirect("manage_rooms")
    else:
        form = RoomForm()
    return render(request, "booking/add_room.html", {"form": form})


@staff_member_required
def edit_room(request, room_id):
    room = get_object_or_404(Room, room_id=room_id)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Room updated successfully.")
            return redirect("manage_rooms")
    else:
        form = RoomForm(instance=room)
    return render(request, "booking/edit_room.html", {"form": form, "room": room})


@staff_member_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    messages.success(request, "Room deleted successfully.")
    return redirect("manage_rooms")

#manage reservation

@staff_member_required
def manage_reservations(request):
    reservations = Reservation.objects.all().order_by("date", "start_time")
    return render(request, "booking/manage_reservations.html", {"reservations": reservations})


@staff_member_required
def add_reservation(request):
    if request.method == "POST":
        form = AdminReservationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Reservation added successfully.")
            return redirect("manage_reservations")
    else:
        form = AdminReservationForm()
    return render(request, "booking/add_reservation.html", {"form": form})


@staff_member_required
def edit_reservation(request, booking_id):
    reservation = get_object_or_404(Reservation, pk=booking_id)
    if request.method == "POST":
        form = AdminReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, "Reservation updated successfully.")
            return redirect("manage_reservations")
    else:
        form = AdminReservationForm(instance=reservation)
    return render(request, "booking/edit_reservation.html", {"form": form})


@staff_member_required
def delete_reservation(request, booking_id):
    reservation = get_object_or_404(Reservation, pk=booking_id)
    reservation.delete()
    messages.success(request, "Reservation deleted successfully.")
    return redirect("manage_reservations")


