from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField


class User(AbstractUser):
    ldap_full_name = models.CharField(max_length=150, blank=True, verbose_name=_('Full name from LDAP'))

    card_number = CardNumberField(null=True, blank=True, unique=True)
