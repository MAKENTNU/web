from typing import Any, Dict, List

from django import forms

from .data_structures import MultiLingualTextStructure
from ..widgets import CKEditorUploadingWidget, CKEditorWidget


class MultiLingualTextEdit(forms.MultiWidget):
    """
    A multi-widget for multilingual fields.
    """
    template_name = 'web/forms/widgets/multi_lingual_text_field.html'

    subwidget_class = forms.TextInput

    def __init__(self, attrs=None, *, languages: List[str] = MultiLingualTextStructure.SUPPORTED_LANGUAGES, subwidget_kwargs: Dict[str, Any] = None):
        self.languages = languages

        widgets = {}
        for language in self.languages:
            # Create widgets from the subwidget class, so we can reuse logic
            subwidget = self.subwidget_class(**{
                'attrs': {
                    **(attrs or {}),
                    # Makes each subwidget distinguishable in the template
                    'language': language,
                },
                # Pass the kwargs to each subwidget (only used by the CKEditor-based widgets)
                **(subwidget_kwargs or {}),
            })
            widgets[language] = subwidget
        super().__init__(widgets, attrs)

    def decompress(self, value):
        """
        Turns the value for the multi-widget into a list of values, one for each sub-widget.

        :param value: The value for the whole multi-widget, either of type None or MultiLingualTextStructure
        :return: A list of values for the individual sub-widgets
        """
        if value is None:
            return [""] * len(self.languages)
        return [value[language] for language in self.languages]

    def get_context(self, name, value, attrs):
        """
        Constructs the context passed to the widget template. This method extends the default multi-widget context with
        the render function of each sub-widget. This, as CKEditor uses the pre-Django 1.11 method of rendering widgets,
        that is through a render function, rather than directly through a template.

        :param name: The name of the widget (e.g. title, content)
        :param value: The value of the multi-widget
        :param attrs: The attributes of the multi-widget
        :return: A context for the template of the multi-widget
        """
        context = super().get_context(name, value, attrs)

        for index, widget in enumerate(self.widgets):
            # Include the render function of the subwidget, as CKEditor does not use templates
            context['widget']['subwidgets'][index]['render'] = widget.render

        return context


class MultiLingualTextInput(MultiLingualTextEdit):
    subwidget_class = forms.TextInput


class MultiLingualTextarea(MultiLingualTextEdit):
    subwidget_class = forms.Textarea


class MultiLingualRichText(MultiLingualTextEdit):
    subwidget_class = CKEditorWidget


class MultiLingualRichTextUploading(MultiLingualTextEdit):
    subwidget_class = CKEditorUploadingWidget
