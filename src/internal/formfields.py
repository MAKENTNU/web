from django import forms

from .util import semester_to_year, year_to_semester
from .validators import semester_string_validator


class SemesterField(forms.CharField):
    default_validators = [semester_string_validator]

    def __init__(self, **kwargs):
        super().__init__(
            **{
                "empty_value": None,
                **kwargs,
            }
        )

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return value
        return semester_to_year(value)

    # Prepares the value before it's passed to the widget [undocumented method]
    def prepare_value(self, value):
        if isinstance(value, float):
            return year_to_semester(value)
        else:
            return super().prepare_value(value)
