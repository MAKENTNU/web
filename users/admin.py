from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from util.admin_utils import DefaultAdminWidgetsMixin
from .models import User


class UserAdmin(DefaultAdminWidgetsMixin, DjangoUserAdmin):
    pass


admin.site.register(User, UserAdmin)
