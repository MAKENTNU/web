from django.contrib import admin

from util.admin_utils import search_escaped_and_unescaped
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import ContentBox


class ContentBoxAdmin(MultiLingualFieldAdmin):
    list_display = ('url_name', 'title', 'last_modified')
    search_fields = ('url_name', 'title', 'content')
    ordering = ('title',)
    readonly_fields = ('last_modified',)

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


admin.site.register(ContentBox, ContentBoxAdmin)
