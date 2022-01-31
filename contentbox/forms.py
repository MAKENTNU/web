from django import forms
from django.conf import settings

from web.multilingual.widgets import MultiLingualRichTextUploading
from .models import ContentBox


class ContentBoxForm(forms.ModelForm):
    class Meta:
        model = ContentBox
        fields = ('content',)


class EditSourceContentBoxForm(ContentBoxForm):
    """
    Enables the user to change the ContentBox's HTML source code directly (including adding ``script`` tags).

    NOTE: Make sure that the user has the ``internal.can_change_rich_text_source`` permission before using this form.
    """

    class Meta(ContentBoxForm.Meta):
        widgets = {
            'content': MultiLingualRichTextUploading(subwidget_kwargs={
                'config_name': settings.CKEDITOR_EDIT_SOURCE_CONFIG_NAME,
            }),
        }
