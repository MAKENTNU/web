from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField


class User(AbstractUser):
    ldap_full_name = models.CharField(max_length=150, blank=True, verbose_name=_('Full name from LDAP'))

    card_number = CardNumberField(unique=True, null=True, blank=True)

    def get_short_full_name(self):
        """
        Retrieves the users first and last name. This shortens the users name
        when it has more than two names. For example, 'Ola Johan Nordmann"
        would become "Ola Nordmann".

        :return: A concatenation of the users two outermost names.
        """
        names = self.get_full_name().split(" ")
        if len(names) <= 2:
            return self.get_full_name()
        return f"{names[0]} {names[-1]}"
