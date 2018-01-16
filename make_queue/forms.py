from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from make_queue.models import Machine
import pytz


# The reservation class is only used for validation of forms, as Semantic UI does not work well with django forms
# in the frontend
class ReservationForm(forms.Form):
    start_time = forms.DateTimeField()
    end_time = forms.DateTimeField()
    machine_type = forms.ChoiceField(
        choices=((machine_type.literal, machine_type.literal) for machine_type in Machine.__subclasses__()))
    event = forms.BooleanField(required=False)
    event_name = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)

        self.fields["machine_name"] = forms.ChoiceField(choices=((machine.pk, machine.name) for machine in Machine.objects.all()))

    def clean_start_time(self):
        # TODO: Change the input to be of the users timezone
        return pytz.timezone("Europe/Oslo").localize(self.cleaned_data["start_time"].replace(tzinfo=None))

    def clean_end_time(self):
        # TODO: Change the input to be of the users timezone
        return pytz.timezone("Europe/Oslo").localize(self.cleaned_data["end_time"].replace(tzinfo=None))

    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        machine_name = cleaned_data["machine_name"]
        machine_type = cleaned_data["machine_type"]

        machine_query = Machine.get_subclass(machine_type).objects.filter(pk=machine_name)

        if not machine_query.exists():
            raise ValidationError("Machine name and machine type does not match")

        cleaned_data["machine"] = machine_query.first()

        if cleaned_data["end_time"] < cleaned_data["start_time"]:
            raise ValidationError("Reservation start time is after end time")

        if cleaned_data["start_time"] < timezone.now():
            raise ValidationError("Reservation starts in the past")

        if cleaned_data["event"] and not cleaned_data["event_name"]:
            raise ValidationError("Event name must have a length of at least 1 for an event")

        return cleaned_data
