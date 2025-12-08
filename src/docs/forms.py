from django import forms
from django.utils.translation import gettext_lazy as _

from web.widgets import CKEditorUploadingWidget
from .models import Content, Page


class AddPageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ("title", "created_by")
        widgets = {
            "created_by": forms.HiddenInput(),
        }


class PageContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ("page", "content", "made_by")
        widgets = {
            "page": forms.HiddenInput(),
            "made_by": forms.HiddenInput(),
        }
        error_messages = {
            "content": {
                "required": _("The page is currently empty; please add some content.")
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Have to set the widget here instead of in `Meta.widgets` above,
        # as the `widget` kwarg is always overwritten in `RichTextUploadingFormField`
        self.fields["content"].widget = CKEditorUploadingWidget()

    def clean(self):
        cleaned_data = super().clean()
        page: Page = cleaned_data.get("page")
        content = cleaned_data.get("content")

        if page and content:
            if page.current_content and content == page.current_content.content:
                message = _(
                    "The content must be changed in order to create a new version."
                )
                raise forms.ValidationError({"content": message})

        return cleaned_data

    def save(self, commit=True):
        instance: Content = super().save(commit=commit)
        page = instance.page
        page.current_content = instance
        page.save()
        return instance


class ChangePageVersionForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ("current_content",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit the choices to the initial ones, to reduce the size of the HTML generated for a non-changing hidden form
        choice = kwargs.get("initial").get("current_content")
        if choice:
            self.fields["current_content"].choices = [(choice.pk, choice)]

    def clean(self):
        cleaned_data = super().clean()
        current_content = cleaned_data.get("current_content")

        # Make sure that the content belongs to the given page
        if current_content:
            if current_content.page != self.instance:
                message = _("The content does not belong to the given page")
                raise forms.ValidationError({"current_content": message})
        return cleaned_data


class DocumentationPageSearchQueryForm(forms.Form):
    query = forms.CharField(required=False, max_length=1000, strip=False)
    page = forms.IntegerField(required=False, min_value=1)
