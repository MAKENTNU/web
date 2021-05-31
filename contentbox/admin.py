from django.contrib import admin

from util.admin_utils import DefaultAdminWidgetsMixin
from .models import ContentBox


class ContentBoxAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ('title', 'last_modified')
    readonly_fields = ('last_modified',)


admin.site.register(ContentBox, ContentBoxAdmin)
