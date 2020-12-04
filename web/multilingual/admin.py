import copy

from django.contrib import admin

from .modelfields import MultiLingualTextField


class MultiLingualFieldAdmin(admin.ModelAdmin):
    """
    Django admin does not render MultiValue fields correctly. This ModelAdmin object overrides the default Django admin
    rendering of the MultiLingual fields.
    """

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Want to override the Django admin fields
        if isinstance(db_field, MultiLingualTextField):
            properties = {}
            for key, value in db_field.widget.__dict__.items():
                try:
                    # Need to perform deep copies in case of mutable properties
                    properties[key] = copy.deepcopy(value)
                except TypeError:
                    # Some class properties are not possible to copy. These will not be mutable anyways
                    properties[key] = value

            # Want to copy widget, as to not override the template for the normal forms
            widget = type("AdminMultiLingualTextField", (db_field.widget,), properties)
            # Different template for admin page, without Fomantic-UI
            widget.template_name = "web/forms/widgets/admin_multi_lingual_text_field.html"
            return db_field.formfield(widget=widget, **kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)
