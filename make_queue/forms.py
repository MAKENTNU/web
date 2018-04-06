from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from make_queue.models import Machine
from news.models import TimePlace


class ReservationForm(forms.Form):
    """Form for creating or changing a reservation"""
    start_time = forms.DateTimeField()
    end_time = forms.DateTimeField()
    machine_type = forms.ChoiceField(
        choices=((machine_type.literal, machine_type.literal) for machine_type in Machine.__subclasses__()))
    event = forms.BooleanField(required=False)
    event_pk = forms.CharField(required=False)
    special = forms.BooleanField(required=False)
    special_text = forms.CharField(required=False, max_length=20)

    def __init__(self, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)

        self.fields["machine_name"] = forms.ChoiceField(
            choices=((machine.pk, machine.name) for machine in Machine.objects.all()))

    def clean(self):
        """
        Cleans and validates the given form

        :return: A dictionary of clean data
        """
        cleaned_data = super().clean()

        # Check that the given machine exists
        machine_query = Machine.get_subclass(cleaned_data["machine_type"]).objects.filter(
            pk=cleaned_data["machine_name"])

        if not machine_query.exists():
            raise ValidationError("Machine name and machine type does not match")

        cleaned_data["machine"] = machine_query.first()

        # Cannot create reservations in the past
        if cleaned_data["start_time"] < timezone.now():
            raise ValidationError("Reservation starts in the past")

        # If the reservation is an event, check that it exists
        if cleaned_data["event"]:
            event_query = TimePlace.objects.filter(pk=cleaned_data["event_pk"])
            if not event_query.exists():
                raise ValidationError("Event must exist")
            cleaned_data["event"] = event_query.first()

        if cleaned_data["event"] and cleaned_data["special"]:
            raise ValidationError("Cannot be both special and event")

        return cleaned_data
