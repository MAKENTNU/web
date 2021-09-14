from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


page_title_regex = r"^[0-9A-Za-z ():]+$"
page_title_validator = RegexValidator(regex=page_title_regex,
                                      message=_("Only numbers, letters, spaces, parentheses and colons are allowed."))
