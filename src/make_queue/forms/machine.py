import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from js_asset import JS

from util.locale_utils import last_week_of_year, year_and_week_to_monday
from util.templatetags.datetime_tags import long_datetime
from web.widgets import MazeMapSearchInput, SemanticChoiceInput
from ..models.machine import Machine, MachineType


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


class MachineDetailQueryForm(forms.Form):
    calendar_year = forms.IntegerField(required=False, min_value=datetime.MINYEAR, max_value=datetime.MAXYEAR)
    calendar_week = forms.IntegerField(required=False, min_value=1, max_value=53)

    def clean(self):
        cleaned_data = super().clean()
        calendar_year = cleaned_data.get('calendar_year')
        calendar_week = cleaned_data.get('calendar_week')

        match calendar_year, calendar_week:
            case None, int():
                raise self._get_all_fields_must_be_set_validation_error()
            case int(), None:
                raise self._get_all_fields_must_be_set_validation_error()

            case int(), int():
                invalid_week = calendar_week > last_week_of_year(calendar_year)
                if not invalid_week:
                    try:
                        year_and_week_to_monday(calendar_year, calendar_week)
                    except ValueError:
                        invalid_week = True

                if invalid_week:
                    raise forms.ValidationError({
                        'calendar_week': forms.ValidationError(f"{calendar_week} is not a valid week number for the year {calendar_year}.",
                                                               code='invalid_calendar_week'),
                    })

        return cleaned_data

    @staticmethod
    def _get_all_fields_must_be_set_validation_error():
        return forms.ValidationError("Either both 'calendar_year' and 'calendar_week' must be set, or none of them.",
                                     code='all_or_no_fields_must_be_set')
