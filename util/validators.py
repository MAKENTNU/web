import re

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


lowercase_slug_regex = re.compile(r"^[a-z0-9_-]+$")
lowercase_slug_validator = RegexValidator(
    regex=lowercase_slug_regex,
    message=_("This can only consist of lowercase English letters, numbers, hyphens or underscores."),
    code='invalid_lowercase_slug',
)
