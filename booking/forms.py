from django import forms
from .models import Reservation, Room

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["room", "date", "start_time", "end_time"]

        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }
