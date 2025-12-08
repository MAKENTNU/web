import copy

import ckeditor.widgets
from django.conf import settings

from .modelfields import MultiLingualTextField
from .widgets import MultiLingualTextEdit


def create_multi_lingual_admin_formfield(
    db_field, request, *, enable_changing_rich_text_source=False, **kwargs
):
    """
    Django admin does not render the MultiLingual fields correctly. This function creates a working widget for
    rendering the MultiLingual fields.
    """
    if not isinstance(db_field, MultiLingualTextField):
        return None

    properties = {}
    for key, value in db_field.widget.__dict__.items():
        try:
            # Need to perform deep copies in case of mutable properties
            properties[key] = copy.deepcopy(value)
        except TypeError:
            # Some class properties are not possible to copy. These will not be mutable anyways
            properties[key] = value

    # Different template for admin page, without Fomantic-UI
    properties["template_name"] = (
        "web/forms/widgets/admin_multi_lingual_text_field.html"
    )
    # Want to copy widget, to not override the template for the normal forms
    base_class = (
        db_field.widget if isinstance(db_field.widget, type) else type(db_field.widget)
    )
    new_widget_type = type("AdminMultiLingualTextField", (base_class,), properties)

    subwidget_kwargs = {}
    assert issubclass(new_widget_type, MultiLingualTextEdit)
    if issubclass(new_widget_type.subwidget_class, ckeditor.widgets.CKEditorWidget):
        if enable_changing_rich_text_source and request.user.has_perm(
            "internal.can_change_rich_text_source"
        ):
            subwidget_kwargs["config_name"] = settings.CKEDITOR_EDIT_SOURCE_CONFIG_NAME

    new_widget = new_widget_type(subwidget_kwargs=subwidget_kwargs)
    return db_field.formfield(widget=new_widget, **kwargs)
