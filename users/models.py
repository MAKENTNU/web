from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField


class User(AbstractUser):
    ldap_full_name = models.CharField(max_length=150, blank=True, verbose_name=_('Full name from LDAP'))

    # Should allow `null` values even when it's a string-based field, as empty strings are checked by the unique constraint
    card_number = CardNumberField(null=True, blank=True, unique=True)

    def get_short_full_name(self):
        """
        Retrieves the user's first and last name. This shortens the user's name
        when they have more than two names. For example, "Ola Johan Nordmann"
        would become "Ola Nordmann".

        :return: A concatenation of the user's two outermost names.
        """
        full_name = self.get_full_name()
        names = full_name.split(" ")
        if len(names) <= 2:
            return full_name
        return f"{names[0]} {names[-1]}"
