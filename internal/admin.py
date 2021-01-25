from django.contrib import admin

from internal.models import Member, Secret, GuidanceHours
from web.multilingual.database import MultiLingualFieldAdmin

from simple_history.admin import SimpleHistoryAdmin


class SecretAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'last_modified')
    search_fields = ('title', 'content')


admin.site.register(Member)
admin.site.register(Secret, SecretAdmin)
admin.site.register(GuidanceHours, SimpleHistoryAdmin)
