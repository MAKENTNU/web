from django import forms

from makerspace.models import Equipment
from web.widgets import SemanticFileInput


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = "__all__"
        widgets = {
            "image": SemanticFileInput(),
        }
