from django import forms
from django.db import models


class UnlimitedCharField(models.TextField):

    def formfield(self, **kwargs):
        return super().formfield(**{
            'widget': forms.CharField.widget,
            **kwargs,
        })


class URLTextField(models.TextField):
    default_validators = models.URLField.default_validators
    description = models.URLField.description

    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': forms.URLField,
            'widget': forms.URLField.widget,  # Overrides TextField's Textarea widget
            **kwargs,
        })
