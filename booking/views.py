from django.shortcuts import render
from .models import Room #importing room model

# Create your views here.

def index(request):
    return render(request, template_name="index.html")

# Create your views here.
# for viewing rooms
def available_rooms(request):
    rooms = Room.objects.all()   # you can filter later if you have "is_available"
    return render(request, "rooms.html", {"rooms": rooms})
