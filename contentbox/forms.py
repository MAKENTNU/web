from django import forms
from django.conf import settings

from web.multilingual.data_structures import MultiLingualTextStructure
from web.multilingual.widgets import MultiLingualRichTextUploading, MultiLingualTextInput
from .models import ContentBox


class ContentBoxForm(forms.ModelForm):
    # The expected names of the subwidgets (one for each language) of `MultiLingualFormField`
    CONTENT_SUBWIDGET_NAMES = [f'content_{language}' for language in MultiLingualTextStructure.SUPPORTED_LANGUAGES]

    class Meta:
        model = ContentBox
        fields = ('title', 'content',)

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

        # Overwrite the form field of `title`
        if self.single_language:
            self.fields['title'] = ContentBox._meta.get_field('title').formfield(
                languages=[self.single_language],
                widget=MultiLingualTextInput(languages=[self.single_language]),
            )

        # Overwrite the form field of `content`
        content_form_field_kwargs = {
            'widget': MultiLingualRichTextUploading(**self.content_extra_widget_kwargs),
        }
        if self.single_language:
            content_form_field_kwargs['languages'] = [self.single_language]
        self.fields['content'] = ContentBox._meta.get_field('content').formfield(**content_form_field_kwargs)

    def clean_title(self):
        title: MultiLingualTextStructure = self.cleaned_data['title']
        if title:
            self._set_same_content_for_languages_if_single_language(title)
        return title

    def clean_content(self):
        content: MultiLingualTextStructure = self.cleaned_data['content']
        if content:
            self._set_same_content_for_languages_if_single_language(content)
        return content

    def _set_same_content_for_languages_if_single_language(self, text_structure: MultiLingualTextStructure):
        if self.single_language:
            single_language_content = text_structure[self.single_language]
            # Set the same JSON content for all languages
            for language in MultiLingualTextStructure.SUPPORTED_LANGUAGES:
                text_structure[language] = single_language_content


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
