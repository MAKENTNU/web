from django.db import models


class UsernameField(models.CharField):
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value:
            value = value.lower()
        return value
