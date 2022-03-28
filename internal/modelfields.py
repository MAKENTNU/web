from django.db import models

from . import formfields
from .util import semester_to_year
from .validators import validate_semester_float


class SemesterField(models.FloatField):
    default_validators = [validate_semester_float]

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, str):
            try:
                return semester_to_year(value)
            except ValueError:
                pass

        return super().get_db_prep_value(value, connection, prepared=prepared)

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': formfields.SemesterField,
            **kwargs,
        })
