from django.core.validators import RegexValidator
from django.forms import CharField
from django.utils.translation import gettext_lazy as _

from card.widgets import CardNumberInput

card_number_validators = (
    RegexValidator(r"^\d{10}$", _("Card number must be ten digits long")),
)


class CardNumberField(CharField):
    """
    Custom form field for card numbers
    """
    widget = CardNumberInput
    default_validators = card_number_validators

    def to_python(self, value):
        value = super().to_python(value)
        if value:
            value = value.zfill(10)
        return value
