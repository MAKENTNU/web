from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelChoiceField, IntegerField
from django.utils.translation import gettext_lazy as _

from make_queue.fields import MachineTypeField, MachineTypeForm
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, ReservationRule, Quota
from news.models import TimePlace
from web.widgets import SemanticTimeInput, SemanticChoiceInput, SemanticSearchableChoiceInput, SemanticDateInput, \
    MazemapSearchInput


class ReservationForm(forms.Form):
    """Form for creating or changing a reservation"""
    start_time = forms.DateTimeField()
    end_time = forms.DateTimeField()
    machine_type = forms.ChoiceField(
        choices=((machine_type.name, machine_type.name) for machine_type in MachineTypeField.possible_machine_types),
        required=False)
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
        machine_query = Machine.objects.filter(pk=cleaned_data["machine_name"])

        if not machine_query.exists():
            raise ValidationError("Machine name and machine type does not match")

        cleaned_data["machine"] = machine_query.first()

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


class QuotaForm(forms.ModelForm):
    class UserModelChoiceField(ModelChoiceField):
        def label_from_instance(self, obj):
            return f'{obj.get_full_name()} - {obj.username}'

    user = UserModelChoiceField(queryset=User.objects.all(),
                                widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
                                label=_("User"),
                                required=False)

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data["user"]
        all_users = cleaned_data["all"]
        if user is None and not all_users:
            raise ValueError("User cannot be None when the quota is not for all users")
        if user is not None and all_users:
            raise ValueError("User cannot be set when the all users is set")
        return cleaned_data

    class Meta:
        model = Quota
        exclude = []


class Printer3DCourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.fields["user"] = ModelChoiceField(
            queryset=User.objects.filter(Q(printer3dcourse=None) | Q(printer3dcourse=self.instance)),
            required=False, widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
            label=Printer3DCourse._meta.get_field('user').verbose_name)
        self.fields["card_number"].required = False

    class Meta:
        model = Printer3DCourse
        exclude = []
        widgets = {
            "status": SemanticChoiceInput(),
            "date": SemanticDateInput(),
            "username": forms.TextInput(attrs={"autofocus": "autofocus"}),
        }


class FreeSlotForm(forms.Form):
    machine_type = MachineTypeForm(
        choices=((machine_type.id, machine_type.name) for machine_type in MachineTypeField.possible_machine_types),
        initial=1, label=_("Machine type"))
    hours = IntegerField(min_value=0, initial=1, label=_("Duration in hours"))
    minutes = IntegerField(min_value=0, max_value=59, initial=0, label=_("Duration in minutes"))


class BaseMachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = "__all__"
        widgets = {
            "status": SemanticChoiceInput(),
            "machine_type": SemanticChoiceInput(),
            "location": MazemapSearchInput(url_field="location_url"),
        }


class CreateMachineForm(BaseMachineForm):
    class Meta(BaseMachineForm.Meta):
        exclude = ["status"]


class EditMachineForm(BaseMachineForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"] = forms.ChoiceField(choices=(
            ("F", _("Available")),
            ("O", _("Out of order")),
            ("M", _("Maintenance")),
        ))

    class Meta(BaseMachineForm.Meta):
        exclude = ["machine_type", "machine_model"]
