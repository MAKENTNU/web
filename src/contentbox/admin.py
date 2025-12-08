from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from util import html_utils
from util.admin_utils import DefaultAdminWidgetsMixin, search_escaped_and_unescaped
from .models import ContentBox


class ContentBoxAdmin(DefaultAdminWidgetsMixin, SimpleHistoryAdmin):
    list_display = (
        "url_name",
        "title",
        "get_extra_change_permissions",
        "last_modified",
    )
    list_filter = (("extra_change_permissions", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("url_name", "title", "content")
    ordering = ("title",)

    filter_horizontal = ("extra_change_permissions",)
    readonly_fields = ("last_modified",)
    enable_changing_rich_text_source = True

    @admin.display(description=_("extra change permissions"))
    def get_extra_change_permissions(self, content_box: ContentBox):
        list_str = html_utils.block_join(
            content_box.extra_change_permissions.all(), sep="<b>&bull;</b>"
        )
        return list_str or None

    def has_change_permission(self, request, obj: ContentBox = None):
        has_base_change_perm = super().has_change_permission(request, obj)
        if not obj:
            return has_base_change_perm

        return has_base_change_perm and request.user.has_perms(
            obj.extra_change_perms_str_tuple
        )

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


admin.site.register(ContentBox, ContentBoxAdmin)
