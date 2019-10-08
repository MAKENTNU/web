from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Card(models.Model):
    """
    Model for connecting a card number to a user
    """
    number = models.fields.CharField(max_length=10, verbose_name=_("Card number"), unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))

    def __str__(self):
        return "EM " + self.number

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
