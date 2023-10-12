from django import forms
from django.db.models import TextChoices
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from news.models import TimePlace
from web.widgets import SemanticChoiceInput
from ..models.machine import Machine, MachineType


class ReservationForm(forms.Form):
    """Form for creating or changing a reservation."""
    start_time = forms.DateTimeField()
    end_time = forms.DateTimeField()
    machine_type = forms.ModelChoiceField(required=False, queryset=MachineType.objects.all())
    event = forms.BooleanField(required=False)
    event_pk = forms.CharField(required=False)
    special = forms.BooleanField(required=False)
    special_text = forms.CharField(required=False, max_length=200)
    comment = forms.CharField(required=False, max_length=2000, initial="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['machine_name'] = forms.ChoiceField(choices=(
            (machine.pk, machine.name) for machine in Machine.objects.all()
        ))

    def clean(self):
        """
        Cleans and validates the given form.

        :return: A dictionary of clean data
        """
        cleaned_data = super().clean()
        machine_pk = cleaned_data.get('machine_name')
        has_event = cleaned_data.get('event')
        event_pk = cleaned_data.get('event_pk')
        is_special = cleaned_data.get('special')

        # Check that the given machine exists
        try:
            cleaned_data['machine'] = Machine.objects.get(pk=machine_pk)
        except Machine.DoesNotExist:
            raise forms.ValidationError("Machine name and machine type do not match")

        # If the reservation is an event, check that it exists
        if has_event:
            if not event_pk:
                raise forms.ValidationError('Event must be specified when the "Event" checkbox is checked')
            if is_special:
                raise forms.ValidationError("Cannot be both special and event")

            event_query = TimePlace.objects.filter(pk=event_pk)
            if not event_query.exists():
                raise forms.ValidationError("Event must exist")
            cleaned_data['event'] = event_query.first()

        return cleaned_data


class ReservationFindFreeSlotsForm(forms.Form):
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by('priority'),
        # `capfirst()` to avoid duplicate translation differing only in case
        label=capfirst(_("machine type")),
        widget=SemanticChoiceInput,
    )
    hours = forms.IntegerField(min_value=0, initial=1, label=_("Duration in hours"))
    minutes = forms.IntegerField(min_value=0, max_value=59, initial=0, label=_("Duration in minutes"))


class ReservationListQueryForm(forms.Form):
    class Owner(TextChoices):
        ME = "me", "Me"
        MAKE = "MAKE", "MAKE"

    owner = forms.TypedChoiceField(choices=Owner.choices, coerce=Owner)


class SLARequestForm(forms.Form):
    description = forms.CharField(widget=forms.Textarea, required=True, label=_("Description"), help_text=_("Provide a description of the object you want us to print and why it should be printed using one of the SLA printers."))
    file = forms.FileField(validators=[FileExtensionValidator(allowed_extensions=["stl"])], required=True, label=_("Upload STL"))
    final_date = forms.DateField(label=_("Final date"), widget=forms.SelectDateWidget, help_text="This field is not required, but if you have a date you need the object within you may provide it here. We do not guarantee to print it within the chosen date, but if we are unable to print within the selected date we will refrain from printing the object at all to save materials.")
