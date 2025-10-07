
from django.urls import path
from booking.views import index, cancellation_success
from . import views

urlpatterns = [
   # path("", index, name="home"),

    path("", views.index, name="index"),
    path("booking/rooms/", views.available_rooms, name="available_rooms"),
    path("booking/reservation/", views.make_reservation, name="make_reservation"),
    path("booking/manage-bookings/", views.manage_bookings, name="manage_bookings"),
    path("booking/edit_booking/<int:booking_id>/", views.edit_booking, name="edit_booking"),
    path("booking/cancel_booking/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("booking/signup/", views.signup_view, name="signup"),
    path("booking/login/", views.login_view, name="login"),
    path("booking/logout/", views.logout_view, name="logout"),
    path("booking/make_reservation/", views.make_reservation, name="make_reservation"),
    path("booking/reservation_success/", views.reservation_success, name="reservation_success"),
    path("booking/cancellation_success/", views.cancellation_success, name="cancellation_success"),

]