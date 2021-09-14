from django.db import models


class UsernameField(models.CharField):

    def get_prep_value(self, value):
        return super().get_prep_value(value).lower()
