from typing import Tuple

from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
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

    @staticmethod
    def get_user_search_fields(prefix='user__', *, annotated_full_name_lookup: str = None) -> Tuple[str, ...]:
        search_fields = []
        search_fields_to_prefix = ['username', 'ldap_full_name', 'email']
        if annotated_full_name_lookup:
            search_fields += [annotated_full_name_lookup]
        else:
            search_fields_to_prefix += ['first_name', 'last_name']
        return tuple(
            search_fields
            + [f'{prefix}{field}' for field in search_fields_to_prefix]
        )

    @staticmethod
    def annotate_full_name(queryset: models.QuerySet['User'], prefix='user__', *, lookup_name: str):
        return queryset.annotate(**{
            lookup_name: Concat(f'{prefix}first_name', Value(' '), f'{prefix}last_name'),
        })
