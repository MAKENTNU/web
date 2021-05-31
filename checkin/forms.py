from django import forms
from django.core.validators import FileExtensionValidator

from .models import UserSkill


class UserSkillForm(forms.ModelForm):
    class Meta:
        model = UserSkill
        fields = ['skill', 'skill_level']


class ProfileImageForm(forms.Form):
    # TODO: move to settings, so that this tuple can also be used by Equipment.image (?)
    allowed_extensions = (
        "bmp",
        "gif",
        "ico",
        "jpeg",
        "jpg",
        "png",
        "tif",
        "tiff",
        "webp",
        "tga",
    )
    image = forms.ImageField(max_length=100, allow_empty_file=False, validators=[FileExtensionValidator(allowed_extensions=allowed_extensions)])
