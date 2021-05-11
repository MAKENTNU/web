from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from card import utils as card_utils
from card.formfields import CardNumberField
from news.models import TimePlace
from users.models import User
from web.widgets import MazemapSearchInput, SemanticChoiceInput, SemanticDateInput, SemanticSearchableChoiceInput, SemanticTimeInput
from .formfields import UserModelChoiceField
from .models.course import Printer3DCourse
from .models.models import Machine, MachineType, Quota, ReservationRule


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


class RuleForm(forms.ModelForm):
    day_field_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    machine_type = forms.ModelChoiceField(MachineType.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = ReservationRule
        fields = ['start_time', 'days_changed', 'end_time', 'max_hours', 'max_inside_border_crossed', 'machine_type']
        widgets = {
            'start_time': SemanticTimeInput(),
            'end_time': SemanticTimeInput(),
            'machine_type': SemanticChoiceInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rule_obj = kwargs["instance"]
        for shift, field_name in enumerate(self.day_field_names):
            self.fields[field_name] = forms.BooleanField(required=False)
            if rule_obj is not None:
                self.fields[field_name].initial = rule_obj.start_days & (1 << shift) > 0

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        rule = ReservationRule(
            machine_type=cleaned_data["machine_type"], max_hours=0, max_inside_border_crossed=0,
            start_time=cleaned_data["start_time"], end_time=cleaned_data["end_time"],
            days_changed=cleaned_data["days_changed"], start_days=self._get_start_days(cleaned_data),
        )
        rule.is_valid_rule(raise_error=True)

        return cleaned_data

    def save(self, commit=True):
        rule = super().save(commit=False)
        rule.start_days = self._get_start_days(self.cleaned_data)
        if commit:
            rule.save()
        return rule

    @staticmethod
    def _get_start_days(cleaned_data):
        return sum(cleaned_data[field_name] << shift for shift, field_name in enumerate(RuleForm.day_field_names))


class QuotaForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset=User.objects.all(),
        widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
        label=_("User"),
        required=False,
    )
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by('priority'),
        label=_("Machine type"),
        empty_label=_("Select machine type"),
        widget=SemanticChoiceInput,
    )

    class Meta:
        model = Quota
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        all_users = cleaned_data.get('all')

        if user is None and not all_users:
            raise forms.ValidationError("User cannot be None when the quota is not for all users")
        if user is not None and all_users:
            raise forms.ValidationError("User cannot be set when the all users is set")
        return cleaned_data


class Printer3DCourseForm(forms.ModelForm):
    card_number = CardNumberField(required=False)

    class Meta:
        model = Printer3DCourse
        exclude = ['_card_number']
        widgets = {
            'status': SemanticChoiceInput(),
            'date': SemanticDateInput(),
            'username': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.fields['user'] = forms.ModelChoiceField(
            queryset=User.objects.filter(Q(printer3dcourse=None) | Q(printer3dcourse=self.instance)),
            required=False,
            widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
            label=Printer3DCourse._meta.get_field('user').verbose_name,
        )
        if self.instance.card_number is not None:
            self.initial['card_number'] = self.instance.card_number

    def clean_card_number(self):
        card_number: str = self.cleaned_data['card_number']
        if card_number:
            # This accident prevention was requested by the Mentor committee.
            # Phone number is from https://innsida.ntnu.no/wiki/-/wiki/Norsk/Vakthold+og+assistanse+utenfor+arbeidstid
            if card_number.lstrip("0") == "91897373":
                raise forms.ValidationError(
                    _("The card number was detected to be the phone number of Building security at NTNU. Please enter a valid card number.")
                )
        return card_number

    def clean(self):
        cleaned_data = super().clean()
        card_number = cleaned_data.get('card_number')
        username = cleaned_data.get('username')

        if card_number and username:
            if card_utils.is_duplicate(card_number, username):
                raise forms.ValidationError({
                    'card_number': _("Card number is already in use"),
                })
        return cleaned_data

    def save(self, commit=True):
        course = super().save(commit=False)
        course.card_number = self.cleaned_data['card_number']
        course.save()
        return course


class FreeSlotForm(forms.Form):
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by('priority'),
        label=_("Machine type"),
        widget=SemanticChoiceInput,
    )
    hours = forms.IntegerField(min_value=0, initial=1, label=_("Duration in hours"))
    minutes = forms.IntegerField(min_value=0, max_value=59, initial=0, label=_("Duration in minutes"))


class BaseMachineForm(forms.ModelForm):
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by('priority'),
        label=_("Machine type"),
        empty_label=_("Select machine type"),
        widget=SemanticChoiceInput,
    )

    class Meta:
        model = Machine
        fields = '__all__'
        widgets = {
            'location': MazemapSearchInput(url_field='location_url'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        status_choices = (
            Machine.Status.AVAILABLE,
            Machine.Status.OUT_OF_ORDER,
            Machine.Status.MAINTENANCE,
        )
        self.fields['status'] = forms.ChoiceField(
            choices=[
                (c, Machine.STATUS_CHOICES_DICT[c])
                for c in status_choices
            ],
            widget=SemanticChoiceInput(attrs={'required': True}),
        )


class EditMachineForm(BaseMachineForm):
    machine_type = None

    class Meta(BaseMachineForm.Meta):
        exclude = ['machine_type', 'machine_model']
