from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.functions import Concat
from django.utils import timezone
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from js_asset import JS

from card import utils as card_utils
from card.formfields import CardNumberField
from news.models import TimePlace
from users.models import User
from util.templatetags.datetime_tags import long_datetime
from web.widgets import (
    Direction, DirectionalCheckboxSelectMultiple, MazeMapSearchInput, SemanticChoiceInput, SemanticDateInput, SemanticSearchableChoiceInput,
    SemanticTimeInput,
)
from .formfields import UserModelChoiceField
from .models.course import Printer3DCourse
from .models.machine import Machine, MachineType
from .models.reservation import Quota, ReservationRule


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


class ReservationRuleForm(forms.ModelForm):
    class Meta:
        model = ReservationRule
        fields = ['start_time', 'days_changed', 'end_time', 'start_days', 'max_hours', 'max_inside_border_crossed', 'machine_type']
        widgets = {
            'start_time': SemanticTimeInput(),
            'end_time': SemanticTimeInput(),
            'start_days': DirectionalCheckboxSelectMultiple(Direction.VERTICAL),
            'machine_type': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        days_changed = cleaned_data.get('days_changed')
        start_days = cleaned_data.get('start_days')
        machine_type: MachineType = cleaned_data.get('machine_type')

        if start_time and end_time and days_changed is not None and start_days and machine_type:
            # Check if the time period is a valid time period (within a week)
            if (start_time > end_time and days_changed == 0
                    or days_changed > 7
                    or days_changed == 7 and start_time < end_time):
                raise forms.ValidationError(_("Period is either too long (7+ days) or start time is earlier than end time."))

            start_days = [int(day) for day in start_days]
            # Check for internal overlap
            time_periods = ReservationRule.Period.list_from_start_weekdays(start_days, start_time, end_time, days_changed)
            if any(t1.overlap(t2)
                   for t1 in time_periods
                   for t2 in time_periods
                   if t1.exact_end_weekday != t2.exact_end_weekday and t1.exact_start_weekday != t2.exact_end_weekday):
                raise forms.ValidationError(_("Rule has internal overlap of time periods."))

            other_reservation_rules = machine_type.reservation_rules.exclude(pk=self.instance.pk)  # pk will be None if creating a new object
            # Check for overlap with other time periods
            other_time_periods = [time_period
                                  for rule in other_reservation_rules
                                  for time_period in rule.time_periods]
            if any(t1.overlap(t2)
                   for t1 in time_periods
                   for t2 in other_time_periods):
                raise forms.ValidationError(_("Rule time periods overlap with time periods of other rules."))

        return cleaned_data


class QuotaForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset=User.objects.order_by(Concat('first_name', 'last_name'), 'username'),
        widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
        # `capfirst()` to avoid duplicate translation differing only in case
        label=capfirst(_("user")),
        required=False,
    )
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by('priority'),
        label=capfirst(_("machine type")),
        empty_label=_("Select machine type"),
        widget=SemanticChoiceInput,
    )

    class Meta:
        model = Quota
        fields = '__all__'

    class Media:
        js = (
            JS('make_queue/js/quota_form.js', attrs={'defer': True}),
        )

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        all_users = cleaned_data.get('all')

        user_error_message = None
        if not user and not all_users:
            user_error_message = _("User must be set when “All users” is not set.")
        if user and all_users:
            user_error_message = _("User cannot be set when “All users” is set.")

        if user_error_message:
            # Can't raise ValidationError when adding errors for both a specific field and the whole form (field=None)
            self.add_error('user', user_error_message)
            self.add_error(None, _("Must select either specific user or all users."))
            return

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
            queryset=User.objects.filter(Q(printer_3d_course=None) | Q(printer_3d_course=self.instance)),
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
            # Phone number is from https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
            if card_number.lstrip("0") == "91897373":
                raise forms.ValidationError(
                    # Translators: See the Norwegian and English versions of this page for
                    # a translation of "Building security":
                    # https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
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


class ReservationFindFreeSlotsForm(forms.Form):
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by('priority'),
        # `capfirst()` to avoid duplicate translation differing only in case
        label=capfirst(_("machine type")),
        widget=SemanticChoiceInput,
    )
    hours = forms.IntegerField(min_value=0, initial=1, label=_("Duration in hours"))
    minutes = forms.IntegerField(min_value=0, max_value=59, initial=0, label=_("Duration in minutes"))


class MachineFormBase(forms.ModelForm):
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by('priority'),
        # `capfirst()` to avoid duplicate translation differing only in case
        label=capfirst(_("machine type")),
        empty_label=_("Select machine type"),
        widget=SemanticChoiceInput(attr_name_to_attr_value_getter={
            'has-stream': lambda iterator_value: iterator_value.instance.has_stream if iterator_value else None,
        }),
    )
    info_message_date = Machine._meta.get_field('info_message_date').formfield(disabled=True)

    class Meta:
        model = Machine
        fields = '__all__'
        widgets = {
            'location': MazeMapSearchInput(url_field='location_url'),
            'info_message': forms.Textarea(attrs={'rows': 5}),
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
        self.fields['info_message_date'].widget.format_value = long_datetime

    def clean(self):
        cleaned_data = super().clean()

        machine_type = cleaned_data.get('machine_type')
        stream_name = cleaned_data.get('stream_name')

        if machine_type:
            if machine_type.has_stream:
                if not stream_name:
                    self.add_error(
                        'stream_name', ValidationError(
                            _("Stream name cannot be empty when the machine type supports streaming."),
                            code='invalid_empty_stream_name',
                        )
                    )
            else:
                # Remove the stream name if the machine type does not support streams
                cleaned_data['stream_name'] = ""

        return cleaned_data


class AddMachineForm(MachineFormBase):
    class Media:
        js = (
            JS('make_queue/js/machine_create.js', attrs={'defer': True}),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Don't show the default value of `info_message_date` in the create form, as it might cause confusion
        self.fields['info_message_date'].widget.format_value = lambda value: None


class ChangeMachineForm(MachineFormBase):
    machine_type = None

    class Meta(MachineFormBase.Meta):
        exclude = ['machine_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.machine_type.has_stream:
            self.fields['stream_name'].disabled = True

    def clean(self):
        # Force the machine type before doing any other cleaning
        self.cleaned_data['machine_type'] = self.instance.machine_type
        cleaned_data = super().clean()

        if 'info_message' in self.changed_data:
            cleaned_data['info_message_date'] = timezone.localtime()

        return cleaned_data
