from django.db import models
from django.db.models.constraints import CheckConstraint
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField
from users.models import User
from .fields import UsernameField


class CoursePermission(models.Model):
    short_name = models.CharField(max_length=4, blank=True, verbose_name=_("short name"), unique=True)
    name = models.CharField(max_length=256, blank=True, verbose_name=_("name"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    def __str__(self):
        return self.name


# `3DPrinterCourse` would be a syntactically invalid name :(
class Printer3DCourse(models.Model):
    class Status(models.TextChoices):
        REGISTERED = 'registered', _("Registered")
        # Translators: See the Norwegian and English versions of this page for
        # a translation of "Building security":
        # https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
        SENT = 'sent', _("Sent to Building security")
        ACCESS = 'access', _("Access granted")

    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        null=True,
        related_name='printer_3d_course',
        verbose_name=_("user"),
    )
    username = UsernameField(max_length=32, blank=True, unique=True, verbose_name=_("username"))
    name = models.CharField(max_length=256, blank=True, verbose_name=_("full name"))
    # Set `null=True` even when it's a string-based field, as `null` is the only value not checked by the unique constraint
    _card_number = CardNumberField(null=True, blank=True, unique=True)  # Card number backing field. Use card_number property instead

    date = models.DateField(verbose_name=_("course date"))
    status = models.CharField(choices=Status.choices, max_length=20, default=Status.REGISTERED, verbose_name=_("status"))
    course_permissions = models.ManyToManyField(CoursePermission, blank=True, verbose_name=_("course permissions"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        constraints = (
            CheckConstraint(check=Q(user__isnull=True) | Q(_card_number__isnull=True), name="user_or_cardnumber_null"),
        )
        verbose_name = _("3D printer course")
        verbose_name_plural = _("3D printer courses")

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
        Connect to user with username if user exists.
        """
        try:
            self.user = User.objects.get(username=self.username)
        except User.DoesNotExist:
            pass

    def get_permission_names(self):
        permissions = self.course_permissions.values_list('short_name', flat=True)
        return permissions

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

    def get_user_display_name(self):
        full_name = self.user.get_full_name() if self.user else self.name
        return str(full_name or self.user or self.username)
