from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from make_queue.models import Machine, ReservationRule
from news.models import TimePlace
from web.widgets import SemanticTimeInput, SemanticChoiceInput


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
    comment = forms.CharField(required=False, max_length=2000, initial="")

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


class RuleForm(forms.ModelForm):
    day_field_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    def __init__(self, *args, **kwargs):
        super(RuleForm, self).__init__(*args, **kwargs)
        rule_obj = kwargs["instance"]
        for shift, field_name in enumerate(self.day_field_names):
            self.fields[field_name] = forms.BooleanField(required=False)
            if rule_obj is not None:
                self.fields[field_name].initial = rule_obj.start_days & (1 << shift) > 0

    def clean(self):
        cleaned_data = super().clean()

        rule = ReservationRule(machine_type=cleaned_data["machine_type"], max_hours=0, max_inside_border_crossed=0,
                               start_time=cleaned_data["start_time"], end_time=cleaned_data["end_time"],
                               days_changed=cleaned_data["days_changed"], start_days=self.get_start_days(cleaned_data))

        rule.is_valid_rule(raise_error=True)

        return cleaned_data

    @staticmethod
    def get_start_days(cleaned_data):
        return sum(cleaned_data[field_name] << shift for shift, field_name in enumerate(RuleForm.day_field_names))

    def save(self, commit=True):
        rule = super(RuleForm, self).save(commit=False)
        rule.start_days = self.get_start_days(self.cleaned_data)
        if commit:
            rule.save()
        return rule

    class Meta:
        model = ReservationRule
        fields = ["start_time", "end_time", "days_changed", "max_hours", "max_inside_border_crossed", "machine_type"]
        widgets = {
            "start_time": SemanticTimeInput(),
            "end_time": SemanticTimeInput(),
            "machine_type": SemanticChoiceInput(),
        }
