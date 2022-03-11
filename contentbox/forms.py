from django import forms
from django.conf import settings

from web.multilingual.data_structures import MultiLingualTextStructure
from web.multilingual.widgets import MultiLingualRichTextUploading
from .models import ContentBox


class ContentBoxForm(forms.ModelForm):
    # The expected names of the subwidgets (one for each language) of `MultiLingualFormField`
    CONTENT_SUBWIDGET_NAMES = [f'content_{language}' for language in MultiLingualTextStructure.SUPPORTED_LANGUAGES]

    class Meta:
        model = ContentBox
        fields = ('content',)

    def __init__(self, *args, single_language: str = False, content_extra_widget_kwargs: dict = None, **kwargs):
        """
        :param single_language: A language code;
                                if set, the form widget of ``content`` will display only this language, and the submitted value for this language
                                will be copied to the other languages used by the website.
        :param content_extra_widget_kwargs: Extra kwargs for the widget of the ``content`` field.
        """
        self.single_language = single_language
        self.content_extra_widget_kwargs = content_extra_widget_kwargs or {}
        if self.single_language:
            self.content_extra_widget_kwargs['languages'] = [self.single_language]

        super().__init__(*args, **kwargs)

        # Overwrite the form field of `content`
        form_field_kwargs = {
            'widget': MultiLingualRichTextUploading(**self.content_extra_widget_kwargs),
        }
        if self.single_language:
            form_field_kwargs['languages'] = [self.single_language]
        self.fields['content'] = ContentBox._meta.get_field('content').formfield(**form_field_kwargs)

    def clean_content(self):
        content: MultiLingualTextStructure = self.cleaned_data['content']
        if content:
            if self.single_language:
                single_language_content = content[self.single_language]
                # Set the same content for all languages
                for language in MultiLingualTextStructure.SUPPORTED_LANGUAGES:
                    content[language] = single_language_content
        return content


class EditSourceContentBoxForm(ContentBoxForm):
    """
    Enables the user to change the ContentBox's HTML source code directly (including adding ``script`` tags).

    NOTE: Make sure that the user has the ``internal.can_change_rich_text_source`` permission before using this form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **{
            'content_extra_widget_kwargs': {
                'subwidget_kwargs': {
                    'config_name': settings.CKEDITOR_EDIT_SOURCE_CONFIG_NAME,
                },
            },
            **kwargs,
        })
