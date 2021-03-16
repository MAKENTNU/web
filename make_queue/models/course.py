from django.db import models
from django.db.models.constraints import CheckConstraint
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField
from users.models import User
from .fields import UsernameField


class Printer3DCourse(models.Model):
    STATUS_CHOICES = (
        ("registered", _("Registered")),
        ("sent", _("Sent to Byggsikring")),
        ("access", _("Access granted")),
    )

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_("User"),
    )
    username = UsernameField(max_length=32, unique=True, verbose_name=_("Username"))
    date = models.DateField(verbose_name=_("Course date"))
    _card_number = CardNumberField(null=True, unique=True)  # Card number backing field. Use card_number property instead
    name = models.CharField(max_length=256, verbose_name=_("Full name"))
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default="registered", verbose_name=_("Status"))
    advanced_course = models.BooleanField(default=False, verbose_name=_("Advanced course"))

    class Meta:
        constraints = (
            CheckConstraint(check=Q(user__isnull=True) | Q(_card_number__isnull=True), name="user_or_cardnumber_null"),
        )

    @property
    def card_number(self):
        if self.user:
            return self.user.card_number
        return self._card_number

    @card_number.setter
    def card_number(self, card_number):
        if self.user:
            self.user.card_number = card_number
            self.user.save()
            self._card_number = None
        else:
            self._card_number = card_number

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None:  # Creation of new object
            self._connect_to_user()
        else:
            old = Printer3DCourse.objects.get(pk=self.pk)
            if old.username != self.username:
                # Changed username, connect to new user
                self._connect_to_user()
            elif self.user:
                # Update username in the rare case that a user changes their username
                self.username = self.user.username

        # If user is set, use card number from user
        if self.user and self._card_number:
            self.user.card_number = self._card_number
            self._card_number = None
            self.user.save()

        super().save(force_insert, force_update, using, update_fields)

    def _connect_to_user(self):
        """
        Connect to user with username if user exists
        """
        try:
            self.user = User.objects.get(username=self.username)
        except User.DoesNotExist:
            pass
