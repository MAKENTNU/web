import copy
import json
from django import forms
from django.db import models
from django.utils.translation import get_language
from json import JSONDecodeError

from web import settings


class MultiLingualTextStructure:
    supported_languages = list(map(lambda language: language[0], settings.LANGUAGES))

    def __init__(self, linear_content, use_default_for_empty):
        self.use_default_for_empty = use_default_for_empty
        self.languages = {language: "" for language in self.supported_languages}
        try:
            for language, value in json.loads(linear_content).items():
                self.languages[language] = value
        except JSONDecodeError:
            self.languages[settings.LANGUAGE_CODE] = linear_content

    def __str__(self):
        return self[get_language()]

    def __getitem__(self, key):
        value = self.languages[key]
        if value or not self.use_default_for_empty:
            return value
        return self.languages[settings.LANGUAGE_CODE]

    def __setitem__(self, key, item):
        self.languages[key] = item


class MultiLingualTextEdit(forms.MultiWidget):
    template_name = "web/forms/widgets/multi_lingual_text_field.html"
    widget = forms.TextInput

    def __init__(self, attrs=None):
        widgets = []
        for language in MultiLingualTextStructure.supported_languages:
            attributes = copy.copy(attrs) or {}
            attributes["language"] = language
            widgets.append(self.widget(attrs=attributes))
        super().__init__(widgets, attrs)

    def decompress(self, value):
        return [value[language] for language in MultiLingualTextStructure.supported_languages]


class MultiLingualTextInput(MultiLingualTextEdit):
    widget = forms.TextInput


class MultiLingualTextarea(MultiLingualTextEdit):
    widget = forms.Textarea


class MultiLingualFormField(forms.MultiValueField):

    def compress(self, data_list):
        structure = MultiLingualTextStructure("", True)
        for index, language in enumerate(structure.supported_languages):
            structure[language] = data_list[index]
        return structure

    def __init__(self, *args, **kwargs):
        defaults = {
            "max_length": kwargs.pop("max_length", None)
        }
        defaults.update(**kwargs)

        fields = []
        for language in MultiLingualTextStructure.supported_languages:
            field_attrs = copy.copy(defaults)
            field_attrs["label"] = f"{field_attrs.get('label')}-{language}"
            field = forms.CharField(**field_attrs)
            field.locale = language
            fields.append(field)

        super().__init__(fields=fields, *args, **kwargs)


class MultiLingualTextField(models.TextField):
    widget = MultiLingualTextInput
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
        defaults = {"form_class": MultiLingualFormField, "widget": self.widget}
        defaults.update(kwargs)
        return super().formfield(**defaults)
