from django import forms
from django.utils.translation import gettext_lazy as _

from web.widgets import SemanticFileInput
from .models import Equipment
from users.models import User


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'
        widgets = {
            'image': SemanticFileInput(),
        }


class CardNumberUpdateForm(forms.ModelForm):
    access_options = [
        ('1', _("I want to register my card after having attended the 3D-printing course")),
        ('2', _("I want to register a new access card")),
        ('3', _("I lost my access to the 3D-printing room, and I want to get it back")),
    ]
    action = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=access_options,
        label=_("Choose the situation that applies to you")
    )

    class Meta:
        model = User
        fields = ['card_number']
        labels = {
            'card_number': _("EM number"),
        }
