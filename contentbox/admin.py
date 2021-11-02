from django.contrib import admin

from web.multilingual.admin import MultiLingualFieldAdmin
from .models import ContentBox


class ContentBoxAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'last_modified')
    readonly_fields = ('last_modified',)


admin.site.register(ContentBox, ContentBoxAdmin)
