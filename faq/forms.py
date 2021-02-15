from django import forms
from django.utils.translation import gettext_lazy as _

from web.widgets import SemanticMultipleSelectInput
from .models import Question


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        widgets = {
            "categories": SemanticMultipleSelectInput(prompt_text=_("Choose categories")),
        }
