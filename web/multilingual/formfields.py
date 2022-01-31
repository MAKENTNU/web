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
    default_error_messages = {
        'required': _("One or more languages have no content."),
    }

    subfield_class = forms.CharField

    def __init__(self, *args, **kwargs):
        subfield_attrs = {
            'max_length': kwargs.pop('max_length', None),
            **kwargs,
            'label': None,  # the `label` attribute is not used by the subfields, so override the one in `kwargs`
        }
        subfields = []
        for language in MultiLingualTextStructure.SUPPORTED_LANGUAGES:
            subfield = self.subfield_class(**subfield_attrs)
            subfield.locale = language
            subfields.append(subfield)

        super().__init__(fields=subfields, *args, **kwargs)

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

        for i, language in enumerate(structure.SUPPORTED_LANGUAGES):
            structure[language] = data_list[i]
        return structure


class MultiLingualRichTextFormField(MultiLingualFormField):
    # Unless we want to emulate the CKEditor code, it requires a different field class for its subfields
    subfield_class = RichTextFormField


class MultiLingualRichTextUploadingFormField(MultiLingualFormField):
    subfield_class = RichTextUploadingFormField
