from django import forms
from web.widgets import SemanticMultipleSelectInput
from django.utils.translation import gettext_lazy as _
from .models import Question, Category


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        widgets = {
            "categories": SemanticMultipleSelectInput(prompt_text=_("Choose categories")),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

