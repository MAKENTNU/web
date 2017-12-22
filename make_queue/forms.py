from django import forms


class ReservationForm(forms.Form):
    start_time = forms.DateTimeField(label="Start tid")
    end_time = forms.DateTimeField(label="Slutt tid")
