from django.contrib import admin
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _

from util.admin_utils import TextFieldOverrideMixin
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Member, Secret, SystemAccess


class MemberAdmin(TextFieldOverrideMixin, admin.ModelAdmin):
    list_display = ('get_name', 'last_modified')
    list_select_related = ('user',)
    readonly_fields = ('last_modified',)

    @admin.display(
        ordering=Concat('user__first_name', 'user__last_name'),
        description=_("Full name"),
    )
    def get_name(self, member: Member):
        return str(member)


class SystemAccessAdmin(admin.ModelAdmin):
    list_display = ('member', 'name', 'value', 'last_modified')
    list_select_related = ('member__user',)
    readonly_fields = ('last_modified',)


class SecretAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'priority', 'last_modified')
    search_fields = ('title', 'content')
    list_editable = ('priority',)
    readonly_fields = ('last_modified',)

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()


admin.site.register(Member, MemberAdmin)
admin.site.register(SystemAccess, SystemAccessAdmin)
admin.site.register(Secret, SecretAdmin)
