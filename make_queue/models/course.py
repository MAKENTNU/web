from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from card.models import Card


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
    card = models.OneToOneField(Card, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=256, verbose_name=_("Full name"))
    status = models.CharField(choices=STATUS_CHOICES, default="registered", max_length=20, verbose_name=_("Status"))

    @property
    def card_number(self):
        if self.card:
            return self.card.number
        return None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Saves the Printer3DCourse object and updates username and the connected card.
        """
        if self.pk is None:  # New object
            self._connect_to_user()
            self._update_card_user()
        else:  # Changing object
            old = Printer3DCourse.objects.get(pk=self.pk)
            if old.user != self.user:
                if self.user:
                    self.username = self.user.username
                else:
                    self._connect_to_user()
                self._update_card_user(old_user=old.user)

            elif old.username != self.username:
                self._connect_to_user()
                self._update_card_user(old_user=old.user)

        super().save(force_insert, force_update, using, update_fields)

    def _update_card_user(self, old_user=None):
        """
        Helper function when saving Printer3DCourse. Only for internal use. Does not call save().
        """
        if old_user:
            self.card.user = None  # Disconnect card from old user to not cause duplication error
            self.card.save(update_course=False)  # Save card but do not propagate change back to Printer3DCourse
        self.card = Card.update_or_create(number=self.card_number, user=self.user, update_course=False)

    def _connect_to_user(self):
        """
        Helper function when saving Printer3DCourse. Only for internal use.  Does not call save().
        """
        user = User.objects.filter(username=self.username)
        self.user = user.first() if user.exists() else None
