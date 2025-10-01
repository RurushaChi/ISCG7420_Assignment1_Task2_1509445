from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Room, Reservation, Profile


# index (homepage)
def index(request):
    return render(request, "booking/index.html")


# signup (create profile)
def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create empty profile for new user
            Profile.objects.create(user=user)
            login(request, user)  # auto login
            messages.success(request, "Account created successfully!")
            return redirect("index")
    else:
        form = UserCreationForm()
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


# make reservation (login required)
@login_required(login_url="login")
def make_reservation(request):
    return render(request, "booking/make_reservation.html")


# manage bookings (only user’s bookings)
@login_required(login_url="login")
def manage_bookings(request):
    reservations = Reservation.objects.filter(user=request.user)
    return render(request, "booking/manage_bookings.html", {"reservations": reservations})