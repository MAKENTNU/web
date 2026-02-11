from django import forms
from django.utils.translation import gettext_lazy as _

from faq.models import Category, Question
from web.widgets import SemanticMultipleSelectInput


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "__all__"
        widgets = {
            "categories": SemanticMultipleSelectInput(
                prompt_text=_("Choose categories")
            ),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
