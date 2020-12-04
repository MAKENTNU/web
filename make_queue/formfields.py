from django import forms

from users.models import User


class UserModelChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj: User):
        return f"{obj.get_full_name()} - {obj.username}"
