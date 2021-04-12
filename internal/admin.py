from django.contrib import admin

from util.admin_utils import TextFieldOverrideMixin
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Member, Secret


class MemberAdmin(TextFieldOverrideMixin, admin.ModelAdmin):
    pass


class SecretAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'last_modified')
    search_fields = ('title', 'content')


admin.site.register(Member, MemberAdmin)
admin.site.register(Secret, SecretAdmin)
