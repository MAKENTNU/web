import copy
import json
from django.contrib import admin
from django.db import models

from web.multilingual.data_structures import MultiLingualTextStructure
from web.multilingual.form import MultiLingualFormField, MultiLingualRichTextFormField, \
    MultiLingualRichTextUploadingFormField
from web.multilingual.widgets import MultiLingualTextInput, MultiLingualRichText, MultiLingualRichTextUploading


class MultiLingualTextField(models.TextField):
    """
    A database field for multilingual text fields
    """
    widget = MultiLingualTextInput
    form_class = MultiLingualFormField
    use_default_if_empty = True

    def __init__(self, *args, **kwargs):
        # Allow for specification of a widget on creation, to allow for both textarea and text input
        self.widget = kwargs.pop("widget", self.widget)
        self.use_default_if_empty = kwargs.pop("use_default_if_empty", self.use_default_if_empty)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """
        Deserialization of the given value
        """
        if value is None:
            return value
        if isinstance(value, MultiLingualTextStructure):
            return value
        return MultiLingualTextStructure(value, self.use_default_if_empty)

    def get_prep_value(self, value):
        """
        Converts the given value to a value that can be saved in the database
        """
        if value is None:
            return value
        if isinstance(value, MultiLingualTextStructure):
            # Save the content as a JSON object with languages as keys
            return json.dumps({language: value[language] for language in value.supported_languages})
        return value

    def from_db_value(self, value, expression, connection):
        """
        Converts the database value to the python representation
        """
        return MultiLingualTextStructure(value, self.use_default_if_empty)

    def formfield(self, **kwargs):
        """
        Sets up the form field
        """
        defaults = {"form_class": self.form_class, "widget": self.widget}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class MultiLingualRichTextField(MultiLingualTextField):
    # CKEditor has specific requirements for its for form class and widget
    widget = MultiLingualRichText
    form_class = MultiLingualRichTextFormField


class MultiLingualRichTextUploadingField(MultiLingualTextField):
    # CKEditor has specific requirements for its for form class and widget
    widget = MultiLingualRichTextUploading
    form_class = MultiLingualRichTextUploadingFormField


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
            # Different template for admin page, without Semantic UI
            widget.template_name = "web/forms/widgets/admin_multi_lingual_text_field.html"
            return db_field.formfield(widget=widget, **kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)
