from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from card.models import CardNumberField, Card


class UsernameField(models.CharField):

    def get_prep_value(self, value):
        return super().get_prep_value(value).lower()


class Printer3DCourse(models.Model):
    STATUS_CHOICES = (
        ("registered", _("Registered")),
        ("sent", _("Sent to Byggsikring")),
        ("access", _("Access granted")),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name=_("User"))
    username = UsernameField(max_length=32, verbose_name=_("Username"), unique=True)
    date = models.DateField(verbose_name=_("Course date"))
    card_number = CardNumberField(unique=True, null=True)
    name = models.CharField(max_length=256, verbose_name=_("Full name"))
    status = models.CharField(choices=STATUS_CHOICES, default="registered", max_length=20, verbose_name=_("Status"))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.card_number and self.user:
            Card.update_or_create(self.user, self.card_number)
        super().save(force_insert, force_update, using, update_fields)
