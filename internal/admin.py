from django.contrib import admin

from util.admin_utils import TextFieldOverrideMixin
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Member, Secret


class MemberAdmin(TextFieldOverrideMixin, admin.ModelAdmin):
    pass


class SecretAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'last_modified', 'priority')
    search_fields = ('title', 'content')
    list_editable = ('priority',)

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()


admin.site.register(Member, MemberAdmin)
admin.site.register(Secret, SecretAdmin)
