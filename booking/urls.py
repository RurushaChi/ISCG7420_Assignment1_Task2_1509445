
from django.urls import path
from booking.views import index
from . import views

urlpatterns = [
    path("", index, name="home"),

    path("rooms/", views.available_rooms, name="available_rooms"),

]