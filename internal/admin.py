from django.contrib import admin

from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Member, Secret


class SecretAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'last_modified')
    search_fields = ('title', 'content')


admin.site.register(Member)
admin.site.register(Secret, SecretAdmin)
