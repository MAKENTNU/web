import copy
import logging

from ckeditor.fields import RichTextFormField
from ckeditor_uploader.fields import RichTextUploadingFormField
from django import forms

from web.multilingual.data_structures import MultiLingualTextStructure


class MultiLingualFormField(forms.MultiValueField):
    """
    A multi-value field for a multilingual database field
    """
    field_class = forms.CharField

    def compress(self, data_list):
        """
        Merges the input from the different form fields into a single value

        :param data_list: A list of the inputs of the different fields
        :return: A MultiLingualTextStructure element
        """
        structure = MultiLingualTextStructure("", True)
        for index, language in enumerate(structure.supported_languages):
            # Non required fields may not have enough values
            try:
                structure[language] = data_list[index]
            except IndexError as e:
                logging.getLogger('django.request').exception(e)
        return structure

    def __init__(self, *args, **kwargs):
        defaults = {
            "max_length": kwargs.pop("max_length", None),
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
    # Unless we want to emulate the CKEditor code, it requires a different field class for its subfields
    field_class = RichTextFormField


class MultiLingualRichTextUploadingFormField(MultiLingualFormField):
    # Unless we want to emulate the CKEditor code, it requires a different field class for its subfields
    field_class = RichTextUploadingFormField
