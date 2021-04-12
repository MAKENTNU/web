from django.contrib.admin.widgets import AdminTextInputWidget, AdminURLFieldWidget

from web.modelfields import URLTextField, UnlimitedCharField


class TextFieldOverrideMixin:
    """Provides the proper widgets for the custom text fields in the Django admin change forms."""
    formfield_overrides = {
        UnlimitedCharField: {'widget': AdminTextInputWidget},
        URLTextField: {'widget': AdminURLFieldWidget},
    }
