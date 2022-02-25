from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from util import html_utils
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import ContentBox


class ContentBoxAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'get_extra_change_permissions', 'last_modified')

    filter_horizontal = ('extra_change_permissions',)
    readonly_fields = ('last_modified',)
    enable_changing_rich_text_source = True

    @admin.display(description=_("extra change permissions"))
    def get_extra_change_permissions(self, content_box: ContentBox):
        return html_utils.block_join(content_box.extra_change_permissions.all(), sep="<b>&bull;</b>") or None

    def has_change_permission(self, request, obj: ContentBox = None):
        has_base_change_perm = super().has_change_permission(request, obj)
        if not obj:
            return has_base_change_perm

        return has_base_change_perm and request.user.has_perms(obj.extra_change_perms_str_tuple)


admin.site.register(ContentBox, ContentBoxAdmin)
