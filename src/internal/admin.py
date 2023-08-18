from django.contrib import admin
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from util import html_utils
from util.admin_utils import DefaultAdminWidgetsMixin, UserSearchFieldsMixin, search_escaped_and_unescaped
from .models import Member, Quote, Secret, SystemAccess, Lore


class MemberAdmin(DefaultAdminWidgetsMixin, SimpleHistoryAdmin):
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
    list_display = ('title', 'priority', 'get_extra_view_permissions', 'last_modified')
    list_filter = (
        ('extra_view_permissions', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('title', 'content')
    list_editable = ('priority',)

    filter_horizontal = ('extra_view_permissions',)
    readonly_fields = ('last_modified',)

    @admin.display(description=_("extra view permissions"))
    def get_extra_view_permissions(self, secret: Secret):
        return html_utils.block_join(secret.extra_view_permissions.all(), sep="<b>&bull;</b>") or None

    def has_add_permission(self, request):
        return self._has_permission(super().has_add_permission(request), request)

    def has_change_permission(self, request, obj: Secret = None):
        return self._has_permission(super().has_change_permission(request, obj), request, obj)

    def has_delete_permission(self, request, obj: Secret = None):
        return self._has_permission(super().has_delete_permission(request, obj), request, obj)

    def has_view_permission(self, request, obj: Secret = None):
        return self._has_permission(super().has_view_permission(request, obj), request, obj)

    @staticmethod
    def _has_permission(has_base_perm, request, obj: Secret = None):
        if not obj:
            return has_base_perm

        return has_base_perm and request.user.has_perms(obj.extra_view_perms_str_tuple)

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


class QuoteAdmin(DefaultAdminWidgetsMixin, UserSearchFieldsMixin, admin.ModelAdmin):
    list_display = ('quote', 'quoted', 'author')
    list_filter = (
        'quoted',
        ('author', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'quote', 'quoted', 'context',
        # The user search fields are appended in `UserSearchFieldsMixin`
    )
    user_lookup, name_for_full_name_lookup = 'author__', 'author_full_name'
    list_select_related = ('author',)

    autocomplete_fields = ('author',)


class LoreAdmin(admin.ModelAdmin):
    ordering = ('title',)
    exclude = ('slug',)


admin.site.register(Member, MemberAdmin)
admin.site.register(SystemAccess, SystemAccessAdmin)
admin.site.register(Secret, SecretAdmin)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(Lore, LoreAdmin)
