from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField
from util.auth_utils import perm_to_str


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
        query = Q()
        for app_label_and_codename in app_labels_and_codenames:
            app_label, codename = app_label_and_codename.split('.', 1)
            query |= Q(content_type__app_label=app_label, codename=codename)
        perms = Permission.objects.filter(query)
        self._check_perms_to_add(perms, app_labels_and_codenames)
        self.user_permissions.add(*perms)

    @staticmethod
    def _check_perms_to_add(filtered_perms, perm_strings_to_add):
        if filtered_perms.count() != len(perm_strings_to_add):
            perm_strings_to_add_set = set(perm_strings_to_add)
            if len(perm_strings_to_add_set) != len(perm_strings_to_add):
                raise ValueError("The permission arguments provided contain duplicates")

            perms_not_found = perm_strings_to_add_set - {perm_to_str(perm) for perm in filtered_perms}
            if not perms_not_found:
                # If all the perm arguments were found, it means that the filtered perms contain duplicate
                # combinations of app labels and codenames, in which case it's fine to just add the duplicates
                return
            perms_not_found_str = ", ".join(f"'{perm}'" for perm in perms_not_found)
            raise Permission.DoesNotExist(f"The following permissions do not exist: {perms_not_found_str}")
