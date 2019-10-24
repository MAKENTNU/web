from django.db import models
from django.utils.translation import gettext_lazy as _

import card.forms


class CardNumberField(models.CharField):
    """
    Custom field for card numbers, doing some extra validation
    """

    def __init__(self, **kwargs):
        kwargs = {
            "verbose_name": _("Card number"),
            **kwargs,
            "validators": card.forms.card_number_validators,
            "max_length": 10,
            "error_messages": {
                "unique": _("Card number already in use"),
            },
        }
        super().__init__(**kwargs)  # No card numbers are more than ten digits long

    def formfield(self, **kwargs):
        if "form_class" not in kwargs:
            kwargs["form_class"] = card.forms.CardNumberField
        return super().formfield(**kwargs)

