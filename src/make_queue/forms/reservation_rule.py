from django import forms
from django.utils.translation import gettext_lazy as _

from web.widgets import Direction, DirectionalCheckboxSelectMultiple, SemanticTimeInput
from ..models.machine import MachineType
from ..models.reservation import ReservationRule


class ReservationRuleForm(forms.ModelForm):
    class Meta:
        model = ReservationRule
        fields = [
            "start_time",
            "days_changed",
            "end_time",
            "start_days",
            "max_hours",
            "max_inside_border_crossed",
            "machine_type",
        ]
        widgets = {
            "start_time": SemanticTimeInput(),
            "end_time": SemanticTimeInput(),
            "start_days": DirectionalCheckboxSelectMultiple(Direction.VERTICAL),
            "machine_type": forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        days_changed = cleaned_data.get("days_changed")
        start_days = cleaned_data.get("start_days")
        machine_type: MachineType = cleaned_data.get("machine_type")

        if (
            start_time
            and end_time
            and days_changed is not None
            and start_days
            and machine_type
        ):
            # Check if the time period is a valid time period (within a week)
            if (
                (start_time > end_time and days_changed == 0)
                or days_changed > 7
                or (days_changed == 7 and start_time < end_time)
            ):
                message = _(
                    "Period is either too long (7+ days) or start time is earlier than end time."
                )
                raise forms.ValidationError(message)

            start_days = [int(day) for day in start_days]
            # Check for internal overlap
            time_periods = ReservationRule.Period.list_from_start_weekdays(
                start_days, start_time, end_time, days_changed
            )
            if any(
                t1.overlap(t2)
                for t1 in time_periods
                for t2 in time_periods
                if t1.exact_end_weekday != t2.exact_end_weekday
                and t1.exact_start_weekday != t2.exact_end_weekday
            ):
                raise forms.ValidationError(
                    _("Rule has internal overlap of time periods.")
                )

            other_reservation_rules = machine_type.reservation_rules.exclude(
                # pk will be None if creating a new object
                pk=self.instance.pk
            )
            # Check for overlap with other time periods
            other_time_periods = [
                time_period
                for rule in other_reservation_rules
                for time_period in rule.time_periods
            ]
            if any(t1.overlap(t2) for t1 in time_periods for t2 in other_time_periods):
                raise forms.ValidationError(
                    _("Rule time periods overlap with time periods of other rules.")
                )

        return cleaned_data
