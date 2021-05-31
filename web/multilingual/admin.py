import copy

from .modelfields import MultiLingualTextField


def create_multi_lingual_admin_formfield(db_field, **kwargs):
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

    # Want to copy widget, as to not override the template for the normal forms
    widget = type('AdminMultiLingualTextField', (db_field.widget,), properties)
    # Different template for admin page, without Fomantic-UI
    widget.template_name = 'web/forms/widgets/admin_multi_lingual_text_field.html'
    return db_field.formfield(widget=widget, **kwargs)
