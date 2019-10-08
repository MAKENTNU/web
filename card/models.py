from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class CardNumberField(models.IntegerField):
    """
    Custom field for card numbers, doing some extra validation
    """
    def __init__(self, **kwargs):
        kwargs.update({
            "validators": (
                 # No card numbers are more than 10 digits long
                 MaxValueValidator(10 ** 10 - 1, _("Card number must be ten digits long")),
                 # Allow for old card numbers and those with 0 as first digit
                 MinValueValidator(10 ** 6, _("Card number must be ten digits long")),
            ),
        })
        super().__init__(**kwargs)


class Card(models.Model):
    """
    Model for connecting a card number to a user
    """
    number = CardNumberField(verbose_name=_("Card number"), unique=True)
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
