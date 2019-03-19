import copy
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from web.multilingual.data_structures import MultiLingualTextStructure


class MultiLingualTextEdit(forms.MultiWidget):
    """
    A multi widget for multilingual fields.
    """
    template_name = "web/forms/widgets/multi_lingual_text_field.html"
    widget = forms.TextInput

    def __init__(self, attrs=None):
        widgets = []
        for language in MultiLingualTextStructure.supported_languages:
            attributes = copy.copy(attrs) or {}
            # Set language in attributes, so each subwidget is distinguishable in the template
            attributes["language"] = language
            # Create widgets from the current set widget class, so we can reuse logic
            widgets.append(self.widget(attrs=attributes))
        super().__init__(widgets, attrs)

    def decompress(self, value):
        """
        Turns the value for the multi widget into a list of values, one for each sub widget

        :param value: The value for the whole multi widget, either of type None or MultiLingualTextStructure
        :return: A list of values for the individual sub widgets
        """
        if value is None:
            return [""] * len(MultiLingualTextStructure.supported_languages)
        return [value[language] for language in MultiLingualTextStructure.supported_languages]

    def get_context(self, name, value, attrs):
        """
        Constructs the context passed to the widget template. This method extends the default multi widget context with
        the render function of each sub widget. This, as CKEditor uses the pre Django 1.11 method of rendering widgets,
        that is through a render function, rather than directly through a template.

        :param name: The name of the widget (e.g. title, content)
        :param value: The value of the multi widget
        :param attrs: The attributes of the multi widget
        :return: A context for the template of the multi widget
        """
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
