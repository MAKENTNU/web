from django import forms

from web.widgets import SemanticFileInput
from .models import Committee


class CommitteeForm(forms.ModelForm):
    class Meta:
        model = Committee
        fields = ("clickbait", "description", "email", "image")
        widgets = {
            "image": SemanticFileInput(),
        }
