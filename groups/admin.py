from django.contrib import admin

from .models import Committee, InheritanceGroup


@admin.register(InheritanceGroup)
class InheritanceGroupAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'parents', 'own_permissions'),
        }),
        ('Inherited permissions', {
            'description': """
                Permissions inherited from parent groups, not including those that overlap
                with this groups own permissions.
            """,
            'classes': ('collapse',),
            'fields': ('inherited_permissions',),
        }),
    )
    filter_horizontal = ('parents', 'own_permissions')
    readonly_fields = ('inherited_permissions',)

    def inherited_permissions(self, obj):
        return '\n'.join(map(str, obj.inherited_permissions))

    inherited_permissions.short_description = 'Inherited permissions'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['parents'].queryset = obj.get_available_parents()
        return form


admin.site.register(Committee)
