import copy

import ckeditor.widgets
from django.conf import settings
from django.contrib import admin

from .modelfields import MultiLingualTextField
from .widgets import MultiLingualTextEdit


class MultiLingualFieldAdmin(admin.ModelAdmin):
    """
    Django admin does not render MultiValue fields correctly. This ModelAdmin object overrides the default Django admin
    rendering of the MultiLingual fields.
    """
    enable_changing_rich_text_source = False

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

            # Different template for admin page, without Fomantic-UI
            properties['template_name'] = 'web/forms/widgets/admin_multi_lingual_text_field.html'
            # Want to copy widget, as to not override the template for the normal forms
            new_widget_type = type("AdminMultiLingualTextField", (db_field.widget,), properties)

            subwidget_kwargs = {}
            assert issubclass(new_widget_type, MultiLingualTextEdit)
            if issubclass(new_widget_type.subwidget_class, ckeditor.widgets.CKEditorWidget):
                if self.enable_changing_rich_text_source and request.user.has_perm('internal.can_change_rich_text_source'):
                    subwidget_kwargs['config_name'] = settings.CKEDITOR_EDIT_SOURCE_CONFIG_NAME

            new_widget = new_widget_type(subwidget_kwargs=subwidget_kwargs)
            return db_field.formfield(widget=new_widget, **kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)
