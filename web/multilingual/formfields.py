import copy

from ckeditor.fields import RichTextFormField
from ckeditor_uploader.fields import RichTextUploadingFormField
from django import forms
from django.utils.translation import gettext_lazy as _

from util.logging_utils import get_request_logger
from .data_structures import MultiLingualTextStructure


class MultiLingualFormField(forms.MultiValueField):
    """
    A multi-value field for a multilingual database field.
    """
    field_class = forms.CharField
    default_error_messages = {
        'required': _("One or more languages have no content."),
    }

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

    def compress(self, data_list):
        """
        Merges the input from the different form fields into a single value.

        :param data_list: A list of the inputs of the different fields
        :return: A MultiLingualTextStructure element
        """
        structure = MultiLingualTextStructure("", True)
        if not data_list:
            return structure
        if len(data_list) != len(structure):
            get_request_logger().exception(
                f"Unexpected number of elements:\n\t{data_list}"
                f"\n\t(Should have matched the number of elements in {repr(structure)})"
            )
            return structure

        for index, language in enumerate(structure.supported_languages):
            structure[language] = data_list[index]
        return structure


class MultiLingualRichTextFormField(MultiLingualFormField):
    # Unless we want to emulate the CKEditor code, it requires a different field class for its subfields
    field_class = RichTextFormField


class MultiLingualRichTextUploadingFormField(MultiLingualFormField):
    # Unless we want to emulate the CKEditor code, it requires a different field class for its subfields
    field_class = RichTextUploadingFormField
