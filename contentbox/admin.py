from django.contrib import admin

from web.multilingual.admin import MultiLingualFieldAdmin
from .models import ContentBox


class ContentBoxAdmin(MultiLingualFieldAdmin):
    list_display = ('url_name', 'last_modified')
    readonly_fields = ('last_modified',)


admin.site.register(ContentBox, ContentBoxAdmin)
