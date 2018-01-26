from django.contrib import admin

from .models import InheritanceGroup, Committee


admin.site.register(Committee)


@admin.register(InheritanceGroup)
class InheritanceGroupAdmin(admin.ModelAdmin):
    readonly_fields = ('inherited_permissions',)
    filter_horizontal = ('parents', 'own_permissions')

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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if obj:
            form.base_fields['parents'].queryset = obj.get_available_parents()

        return form

    def inherited_permissions(self, instance):
        permissions = set(instance.permissions.all()) - set(instance.own_permissions.all())
        return '\n'.join(map(lambda x: str(x), permissions))

    inherited_permissions.short_description = 'Inherited permissions'
