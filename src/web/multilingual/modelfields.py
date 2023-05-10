import json

from django.db import models

from .data_structures import MultiLingualTextStructure
from .formfields import MultiLingualFormField, MultiLingualRichTextFormField, MultiLingualRichTextUploadingFormField
from .widgets import MultiLingualRichText, MultiLingualRichTextUploading, MultiLingualTextEdit, MultiLingualTextInput


class MultiLingualTextField(models.TextField):
    """
    A database field for multilingual text fields.
    """
    widget = MultiLingualTextInput
    form_class = MultiLingualFormField
    languages = MultiLingualTextStructure.SUPPORTED_LANGUAGES
    use_default_if_empty = True

    def __init__(self, *args, widget=None, languages=None, **kwargs):
        # Allow for specification of a widget on creation, to allow for both textarea and text input
        self.widget = widget or self.widget
        self.languages = languages or self.languages
        if isinstance(self.widget, type) and issubclass(self.widget, MultiLingualTextEdit):
            self.widget = self.widget(languages=self.languages)
        self.use_default_if_empty = kwargs.pop('use_default_if_empty', self.use_default_if_empty)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """
        Deserialization of the given value.
        """
        if value is None:
            return value
        if isinstance(value, MultiLingualTextStructure):
            return value
        return MultiLingualTextStructure(value, languages=self.languages, use_default_for_empty=self.use_default_if_empty)

    def get_prep_value(self, value):
        """
        Converts the given value to a value that can be saved in the database.
        """
        if value is None:
            return value
        if isinstance(value, MultiLingualTextStructure):
            # Save the content as a JSON object with languages as keys
            return json.dumps(
                value.languages,
                ensure_ascii=False,  # Prevents replacing unicode characters with \u encoding, which would have messed with searching
            )
        return value

    def from_db_value(self, value, *args, **kwargs):
        """
        Converts the database value to the Python representation.
        """
        return MultiLingualTextStructure(value, languages=self.languages, use_default_for_empty=self.use_default_if_empty)

    def formfield(self, **kwargs):
        """
        Sets up the form field.
        """
        defaults = {
            'form_class': self.form_class,
            'widget': self.widget,
        }
        if issubclass(self.form_class, MultiLingualFormField):
            defaults['languages'] = self.languages

        defaults.update(kwargs)
        return super().formfield(**defaults)


class MultiLingualRichTextField(MultiLingualTextField):
    # CKEditor has specific requirements for its form class and widget
    widget = MultiLingualRichText
    form_class = MultiLingualRichTextFormField


class MultiLingualRichTextUploadingField(MultiLingualTextField):
    # CKEditor has specific requirements for its form class and widget
    widget = MultiLingualRichTextUploading
    form_class = MultiLingualRichTextUploadingFormField
