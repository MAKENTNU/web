from django import forms

from docs.models import Content, Page


class CreatePageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = (
            "title",
        )


class PageContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = (
            "content",
        )
