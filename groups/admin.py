from django.contrib import admin

from .models import Committee, InheritanceGroup


class InheritanceGroupAdmin(admin.ModelAdmin):
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
    )
    filter_horizontal = ('parents', 'own_permissions')
    readonly_fields = ('get_inherited_permissions',)

    @admin.display(description="Inherited permissions")
    def get_inherited_permissions(self, inheritance_group: InheritanceGroup):
        return "\n".join(map(str, inheritance_group.inherited_permissions))

    def get_form(self, request, obj: InheritanceGroup = None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['parents'].queryset = obj.get_available_parents()
        return form


admin.site.register(InheritanceGroup, InheritanceGroupAdmin)
admin.site.register(Committee)
