import re
from collections.abc import Collection

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class WhitelistedEmailValidator(EmailValidator):
    message = _("Enter a valid email address ending in “@makentnu.no”.")

    def __init__(self, valid_domains: Collection[str], **kwargs):
        super().__init__(**kwargs)
        self.valid_domains = set(valid_domains)

    def validate_domain_part(self, domain_part):
        return domain_part in self.valid_domains


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


discord_username_regex = re.compile(r'^(.+)#([0-9]{4})$')
discord_username_validator = RegexValidator(
    discord_username_regex,
    _("Enter a valid Discord username – including the hashtag and the four digits at the end."),
)
