from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from util.admin_utils import DefaultAdminWidgetsMixin
from .models import Committee, InheritanceGroup


class InheritanceGroupAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'last_modified')

    fieldsets = (
        (None, {
            'fields': ('name', 'parents', 'own_permissions'),
        }),
        ('Inherited permissions', {
            'description': """
                Permissions inherited from parent groups, not including those that overlap
                with this group's own permissions.
            """,
            'classes': ('collapse',),
            'fields': ('get_inherited_permissions',),
        }),
        (None, {
            'fields': ('last_modified',),
        }),
    )
    filter_horizontal = ('parents', 'own_permissions')
    readonly_fields = ('last_modified', 'get_inherited_permissions',)

    @admin.display(description="Inherited permissions")
    def get_inherited_permissions(self, inheritance_group: InheritanceGroup):
        return "\n".join(map(str, inheritance_group.inherited_permissions))

    def get_form(self, request, obj: InheritanceGroup = None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['parents'].queryset = obj.get_available_parents()
        return form


class CommitteeAdmin(DefaultAdminWidgetsMixin, SimpleHistoryAdmin):
    list_display = ('name', 'last_modified')
    list_select_related = ('group',)

    readonly_fields = ('last_modified',)


admin.site.register(InheritanceGroup, InheritanceGroupAdmin)
admin.site.register(Committee, CommitteeAdmin)
