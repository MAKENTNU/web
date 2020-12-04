from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Content, Page


class CreatePageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ('title',)


class PageContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ('content',)


class ChangePageVersionForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ('current_content',)

    def __init__(self, *args, **kwargs):
        super(ChangePageVersionForm, self).__init__(*args, **kwargs)

        # Limit the choices to the initial ones, to reduce the size of the HTML generated for a non-changing hidden form
        choice = kwargs.get('initial').get('current_content')
        self.fields['current_content'].choices = [(choice.pk, choice)]

    def clean(self):
        cleaned_data = super().clean()
        current_content = cleaned_data['current_content']

        # Make sure that the content belongs to the given page
        if current_content:
            if current_content.page != self.instance:
                raise forms.ValidationError({
                    'current_content': _("The content does not belong to the given page"),
                })
        return cleaned_data
