from django.contrib import admin
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from util.admin_utils import DefaultAdminWidgetsMixin, UserSearchFieldsMixin, search_escaped_and_unescaped
from .models import Member, Secret, SystemAccess


class MemberAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ('get_name', 'last_modified')
    list_select_related = ('user',)

    autocomplete_fields = ('user',)
    filter_horizontal = ('committees',)
    readonly_fields = ('last_modified',)

    @admin.display(
        ordering=Concat('user__first_name', 'user__last_name'),
        description=_("full name"),
    )
    def get_name(self, member: Member):
        return str(member)


class SystemAccessAdmin(UserSearchFieldsMixin, admin.ModelAdmin):
    list_display = ('member', 'name', 'value', 'last_modified')
    list_filter = ('name', 'value')
    search_fields = (
        # The user search fields are appended in `UserSearchFieldsMixin`
    )
    user_lookup, name_for_full_name_lookup = 'member__user__', 'member_full_name'
    list_select_related = ('member__user',)

    readonly_fields = ('last_modified',)


class SecretAdmin(DefaultAdminWidgetsMixin, SimpleHistoryAdmin):
    list_display = ('title', 'priority', 'last_modified')
    search_fields = ('title', 'content')
    list_editable = ('priority',)

    readonly_fields = ('last_modified',)

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


admin.site.register(Member, MemberAdmin)
admin.site.register(SystemAccess, SystemAccessAdmin)
admin.site.register(Secret, SecretAdmin)
