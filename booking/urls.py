
from django.urls import path
from booking.views import index
from . import views

urlpatterns = [
   # path("", index, name="home"),

    path("", views.index, name="index"),
    path("booking/rooms/", views.available_rooms, name="available_rooms"),
    path("booking/reservation/", views.make_reservation, name="make_reservation"),
    path("booking/manage-bookings/", views.manage_bookings, name="manage_bookings"),
    path("booking/signup/", views.signup_view, name="signup"),
    path("booking/login/", views.login_view, name="login"),
    path("booking/logout/", views.logout_view, name="logout"),

]