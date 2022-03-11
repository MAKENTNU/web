from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField
from util.auth_utils import get_perms


class User(AbstractUser):
    ldap_full_name = models.CharField(max_length=150, blank=True, verbose_name=_("full name from LDAP"))

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

    def has_any_permissions_for(self, model: models.Model):
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        return any(self.has_perm(f'{app_label}.{action}_{model_name}') for action in ('add', 'change', 'delete'))

    def add_perms(self, *app_labels_and_codenames: str):
        perms = get_perms(*app_labels_and_codenames)
        self.user_permissions.add(*perms)
