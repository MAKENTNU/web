from django import forms

from groups.models import Committee
from web.widgets import SemanticFileInput


class CommitteeForm(forms.ModelForm):
    class Meta:
        model = Committee
        fields = ("clickbait", "description", "email", "image")
        widgets = {
            "image": SemanticFileInput(),
        }
