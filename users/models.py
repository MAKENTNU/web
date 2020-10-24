from django.contrib.auth.models import AbstractUser

from card.models import CardNumberField


class User(AbstractUser):
    card_number = CardNumberField(unique=True, null=True, blank=True)
