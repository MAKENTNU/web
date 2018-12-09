import copy
from ckeditor.fields import RichTextFormField
from ckeditor_uploader.fields import RichTextUploadingFormField
from django import forms

from web.multilingual.data_structures import MultiLingualTextStructure


class MultiLingualFormField(forms.MultiValueField):
    field_class = forms.CharField

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
            field = self.field_class(**field_attrs)
            field.locale = language
            fields.append(field)

        super().__init__(fields=fields, *args, **kwargs)


class MultiLingualRichTextFormField(MultiLingualFormField):
    field_class = RichTextFormField


class MultiLingualRichTextUploadingFormField(MultiLingualFormField):
    field_class = RichTextUploadingFormField
