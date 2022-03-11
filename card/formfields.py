from django import forms
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from .validators import card_number_input_validator
from .widgets import CardNumberInput


class CardNumberField(forms.CharField):
    """
    Custom form field for card numbers.
    """
    widget = CardNumberInput
    default_validators = [card_number_input_validator]

    def __init__(self, **kwargs):
        super().__init__(**{
            'empty_value': None,
            # `capfirst()` to avoid duplicate translation differing only in case
            'label': capfirst(_("card number")),
            **kwargs,
        })

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return value
        return value.zfill(10)
