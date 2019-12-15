from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from docs.models import Content


class PageContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = (
            "content",
        )
