from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import card_number_validator


class CardNumberField(models.CharField):
    """
    Custom field for card numbers, doing some extra validation.
    """
    empty_strings_allowed = False  # empty values should be stored as None
    default_validators = [card_number_validator]

    def __init__(self, **kwargs):
        super().__init__(**{
            'verbose_name': _("card number"),
            'max_length': 10,  # No card numbers are more than ten digits long
            'error_messages': {
                'unique': _("Card number already in use"),
            },
            **kwargs,
        })

    def formfield(self, **kwargs):
        from . import formfields  # Avoids circular importing

        return super().formfield(**{
            'form_class': formfields.CardNumberField,
            **kwargs,
        })

    def get_prep_value(self, value):
        match value:
            case CardNumber():
                return str(value.number)
            case str():
                value = value.strip()
                # Only try to remove an EM prefix if the string is not just whitespace
                if value:
                    return value.split()[-1]  # Remove possible EM prefix
            case _:
                # `value` is either None or not an acceptable value
                return None

    def from_db_value(self, value, *args, **kwargs):
        if value:
            return CardNumber(value)
        return None


class CardNumber:
    """
    Object used to print card numbers with prefix.
    """

    def __init__(self, number):
        self.number = str(number)

    def __str__(self):
        return f"EM {self.number}"
