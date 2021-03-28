import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


semester_string_regex = re.compile(r'^([VH])(\d{2}|\d{4})$', re.IGNORECASE)
# Used for validating user input through the form field
semester_string_validator = RegexValidator(semester_string_regex, _("Enter a valid format for a semester."))


# Used for validating the model field
def validate_semester_float(value):
    # If `value` does not end in .0 or .5:
    if value % 1 not in {0, 0.5}:
        raise ValidationError(
            "%(value)s is not a valid semester float",
            params={'value': value},
        )
