from django import forms

from web.widgets import SemanticFileInput
from .models import Equipment


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'
        widgets = {
            'image': SemanticFileInput(),
        }
