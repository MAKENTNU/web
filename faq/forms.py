from django import forms
from web.widgets import SemanticMultipleSelectInput
from django.utils.translation import gettext_lazy as _
from .models import Question


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["title", "answer", "categories"]
        widgets = {
            "categories": SemanticMultipleSelectInput(prompt_text=_("Choose categories")),
        }
