import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .validators import card_number_validator
from .widgets import CardNumberInput


class CardNumberField(forms.CharField):
    """
    Custom form field for card numbers
    """
    widget = CardNumberInput
    default_validators = [card_number_validator]

    def __init__(self, **kwargs):
        super().__init__(**{
            "label": _("Card number"),
            **kwargs,
        })

    def to_python(self, value):
        value = super().to_python(value)
        if not value:
            return None
        if not re.match(r"^\d{7,10}$", value):
            raise ValidationError(_("Card number must be between seven and ten digits long."))

        return value.zfill(10)
