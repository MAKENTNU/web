from typing import Tuple

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


def get_user_search_fields(prefix='user__') -> Tuple[str, ...]:
    return tuple(f'{prefix}{field}' for field in
                 ('username', 'first_name', 'last_name', 'ldap_full_name', 'email'))


class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'card_number', 'is_staff', 'is_superuser')
    search_fields = (*get_user_search_fields(prefix=''), 'card_number')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_("Personal info"), {'fields': ('first_name', 'last_name', 'ldap_full_name', 'email')}),
        (_("Other info"), {'fields': ('card_number',)}),
        (_("Permissions"), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_("Important dates"), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('ldap_full_name',)


admin.site.register(User, UserAdmin)
