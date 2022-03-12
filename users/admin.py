from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.template.defaultfilters import urlize
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from util.admin_utils import DefaultAdminWidgetsMixin, UserSearchFieldsMixin
from .models import User


class UserAdmin(DefaultAdminWidgetsMixin, UserSearchFieldsMixin, DjangoUserAdmin):
    list_display = (
        'username', 'get_email', 'first_name', 'last_name', 'card_number', 'is_staff', 'is_superuser',
        'date_joined', 'last_login',
    )
    search_fields = (
        'card_number',
        # The user search fields are appended in `UserSearchFieldsMixin`
    )
    user_lookup, name_for_full_name_lookup = '', 'full_name'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        # `capfirst()` to avoid duplicate translation differing only in case
        (capfirst(_("personal info")), {'fields': ('first_name', 'last_name', 'ldap_full_name', 'email')}),
        (capfirst(_("other info")), {'fields': ('card_number',)}),
        (capfirst(_("permissions")), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (capfirst(_("important dates")), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('ldap_full_name', 'last_login', 'date_joined')

    @admin.display(
        ordering='email',
        description=_("email"),
    )
    def get_email(self, user: User):
        return urlize(user.email) or None


admin.site.register(User, UserAdmin)
