from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


# Used for validating user input through the form field
card_number_input_validator = RegexValidator(
    r"^\d{7,10}$", _("Card number must be between seven and ten digits long.")
)
# Used for validating the model field
card_number_validator = RegexValidator(
    r"^\d{10}$", _("Card number must be ten digits long.")
)
