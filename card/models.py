from django.contrib.auth.models import User
from django.core.validators import RegexValidator
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
            "validators": (
                RegexValidator(r"\d{10}", _("Card number must be ten digits long")),
            ),
            "max_length": 10,
        }
        super().__init__(**kwargs)  # No card numbers are more than ten digits long

    def formfield(self, **kwargs):
        if "form_class" not in kwargs:
            kwargs["form_class"] = card.forms.CardNumberField
        return super().formfield(**kwargs)


class Card(models.Model):
    """
    Model for connecting a card number to a user
    """
    number = CardNumberField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))

    def __str__(self):
        return "EM " + str(self.number)

    @classmethod
    def update_or_create(cls, user, number):
        """
        Checks if the user has a card already. Updates the card number if it has, creates a card if it hasn't.
        :param user: The user whose card number to set
        :param number: The card number to attach to the user
        """
        if hasattr(user, 'card'):
            user.card.number = number
            user.card.save()
        else:
            cls.objects.create(user=user, number=number)
