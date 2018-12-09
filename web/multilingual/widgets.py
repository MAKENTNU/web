import copy
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from web.multilingual.data_structures import MultiLingualTextStructure


class MultiLingualTextEdit(forms.MultiWidget):
    template_name = "web/forms/widgets/multi_lingual_text_field.html"
    widget = forms.TextInput

    def __init__(self, attrs=None):
        widgets = []
        for language in MultiLingualTextStructure.supported_languages:
            attributes = copy.copy(attrs) or {}
            attributes["language"] = language
            widgets.append(self.create_widget(attributes))
        super().__init__(widgets, attrs)

    def create_widget(self, attributes):
        return self.widget(attrs=attributes)

    def decompress(self, value):
        if value is None:
            return [""] * len(MultiLingualTextStructure.supported_languages)
        return [value[language] for language in MultiLingualTextStructure.supported_languages]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        for index, widget in enumerate(self.widgets):
            # Include the render function of the subwidget, as CKEditor does not use templates
            context["widget"]["subwidgets"][index]["render"] = widget.render

        return context


class MultiLingualTextInput(MultiLingualTextEdit):
    widget = forms.TextInput


class MultiLingualTextarea(MultiLingualTextEdit):
    widget = forms.Textarea


class MultiLingualRichText(MultiLingualTextEdit):
    widget = CKEditorWidget


class MultiLingualRichTextUploading(MultiLingualTextEdit):
    widget = CKEditorUploadingWidget
