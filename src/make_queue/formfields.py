from django import forms
from django.utils.safestring import mark_safe

from users.models import User


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: User):
        return mark_safe(f"{obj.get_full_name()} &nbsp;&ndash;&nbsp; {obj.username}")
