import json
from django.db import models

from web.multilingual.data_structures import MultiLingualTextStructure
from web.multilingual.form import MultiLingualFormField, MultiLingualRichTextFormField, \
    MultiLingualRichTextUploadingFormField
from web.multilingual.widgets import MultiLingualTextInput, MultiLingualRichText, MultiLingualRichTextUploading


class MultiLingualTextField(models.TextField):
    widget = MultiLingualTextInput
    form_class = MultiLingualFormField
    use_default_if_empty = True

    def __init__(self, *args, **kwargs):
        self.widget = kwargs.pop("widget", self.widget)
        self.use_default_if_empty = kwargs.pop("use_default_if_empty", self.use_default_if_empty)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, MultiLingualTextStructure):
            return value
        return MultiLingualTextStructure(value, self.use_default_if_empty)

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, MultiLingualTextStructure):
            return json.dumps({language: value[language] for language in value.supported_languages})
        return value

    def from_db_value(self, value, expression, connection):
        return MultiLingualTextStructure(value, self.use_default_if_empty)

    def formfield(self, **kwargs):
        defaults = {"form_class": self.form_class, "widget": self.widget}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class MultiLingualRichTextField(MultiLingualTextField):
    widget = MultiLingualRichText
    form_class = MultiLingualRichTextFormField


class MultiLingualRichTextUploadingField(MultiLingualTextField):
    widget = MultiLingualRichTextUploading
    form_class = MultiLingualRichTextUploadingFormField
