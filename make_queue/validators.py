import re

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


machine_stream_name_regex = re.compile(r"^[a-z0-9_-]+$")
machine_stream_name_validator = RegexValidator(
    regex=machine_stream_name_regex,
    message=_("This can only consist of lowercase English letters, numbers, hyphens or underscores."),
    code='invalid_stream_name',
)
