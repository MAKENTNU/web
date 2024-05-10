from django import forms
from django.db import models
from multiselectfield import MultiSelectField as MSField


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


class MultiSelectField(MSField):
    """
    Custom Implementation of MultiSelectField to achieve Django 5.0 compatibility
    #TODO remove when MultiSelectField fully supports Django 5.0

    See: https://github.com/goinnn/django-multiselectfield/issues/141#issuecomment-1911731471
    """

    def _get_flatchoices(self):
        flat_choices = super(models.CharField, self).flatchoices

        class MSFFlatchoices(list):
            # Used to trick django.contrib.admin.utils.display_for_field into not treating the list of values as a
            # dictionary key (which errors out)
            def __bool__(self):
                return False

            __nonzero__ = __bool__

        return MSFFlatchoices(flat_choices)

    flatchoices = property(_get_flatchoices)
