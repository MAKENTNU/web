from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


card_number_validator = RegexValidator(r"^\d{10}$", _("Card number must be ten digits long."))
