from functools import cached_property

from django.db import models
from django.db.models.constraints import CheckConstraint
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _

from card.modelfields import CardNumberField
from make_queue.models.fields import UsernameField
from users.models import User


class CoursePermission(models.Model):
    class DefaultPerms(models.TextChoices):
        IS_AUTHENTICATED = "AUTH", _("Only has to be logged in")
        TAKEN_3D_PRINTER_COURSE = "3DPR", _("Taken the 3D printer course")
        TAKEN_RAISE3D_COURSE = "R3DP", _("Taken the course on Raise3D printers")
        SLA_PRINTER_COURSE = "SLAP", _("Taken the SLA 3D printer course")

    short_name = models.CharField(
        max_length=4, blank=True, verbose_name=_("short name"), unique=True
    )
    name = models.CharField(max_length=256, blank=True, verbose_name=_("name"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    def __str__(self):
        return self.name


# `3DPrinterCourse` would be a syntactically invalid name :(
class Printer3DCourse(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered", _("Registered")
        # Translators: See the Norwegian and English versions of this page for
        # a translation of "Building security": https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
        SENT = "sent", _("Sent to Building security")
        ACCESS = "access", _("Access granted")

    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        null=True,
        related_name="printer_3d_course",
        verbose_name=_("user"),
    )
    username = UsernameField(
        max_length=32, blank=True, unique=True, verbose_name=_("username")
    )
    name = models.CharField(max_length=256, blank=True, verbose_name=_("full name"))
    # Set `null=True` even when it's a string-based field, as `null` is the only value
    # not checked by the unique constraint
    # (Card number backing field. Use card_number property instead)
    _card_number = CardNumberField(null=True, blank=True, unique=True)

    date = models.DateField(verbose_name=_("course date"))
    status = models.CharField(
        choices=Status.choices,
        max_length=20,
        default=Status.REGISTERED,
        verbose_name=_("status"),
    )
    course_permissions = models.ManyToManyField(
        CoursePermission, blank=True, verbose_name=_("course permissions")
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        constraints = (
            CheckConstraint(
                check=Q(user__isnull=True) | Q(_card_number__isnull=True),
                name="user_or_cardnumber_null",
            ),
        )
        verbose_name = _("3D printer course")
        verbose_name_plural = _("3D printer courses")

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
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

    @cached_property
    def permission_names(self) -> list[str]:
        return [perm.short_name for perm in self.course_permissions.all()]

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


class CourseRegistrationConfirmation(models.Model):
    """
    Something a course participant has to confirm before asking to be registered.

    The statements are edited in the admin panel, so that they can be reworded - or
    new ones added - without a deployment.
    """

    text = models.CharField(max_length=500, verbose_name=_("text"))
    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=_("Only the active statements have to be confirmed."),
    )
    priority = models.IntegerField(
        default=0,
        verbose_name=_("priority"),
        help_text=_("The statements are sorted ascending by this value."),
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        ordering = ("priority", "pk")
        verbose_name = _("course registration confirmation")
        verbose_name_plural = _("course registration confirmations")

    def __str__(self):
        return self.text


class CourseRegistrationRequest(models.Model):
    """
    A logged-in user asking to be registered as having taken the 3D printer course.

    This is deliberately kept separate from :class:`Printer3DCourse`, as merely having
    a ``Printer3DCourse`` grants access to the 3D printers (see
    ``Machine.can_use_3d_printer()``) - a request must therefore be approved by someone
    with the permission to do so before it becomes a registration.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Awaiting approval")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="course_registration_requests",
        verbose_name=_("user"),
    )
    # Not unique, as the card number is only moved onto the user when the request is
    # approved; until then, two users may well have submitted the same (mistyped) one
    card_number = CardNumberField(null=True, blank=True, verbose_name=_("card number"))
    course_date = models.DateField(verbose_name=_("course date"))
    # Kept as a record of what was confirmed, as the statements can change later
    confirmations = models.ManyToManyField(
        to=CourseRegistrationConfirmation,
        blank=True,
        related_name="registration_requests",
        verbose_name=_("confirmations"),
    )
    status = models.CharField(
        choices=Status.choices,
        max_length=20,
        default=Status.PENDING,
        verbose_name=_("status"),
    )
    submitted = models.DateTimeField(auto_now_add=True, verbose_name=_("submitted"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(status="pending"),
                name="%(class)s_at_most_one_pending_request_per_user",
            ),
        )
        ordering = ("submitted",)
        verbose_name = _("course registration request")
        verbose_name_plural = _("course registration requests")

    def __str__(self):
        return f"{self.user} - {self.get_status_display()}"

    def approve(self, course_permissions) -> Printer3DCourse:
        """
        Turn the request into a course registration.

        :param course_permissions: The permissions to give the registration, in
                                   addition to the 3D printer course permission
        :return: The created registration
        """
        registration = Printer3DCourse(
            username=self.user.username,
            name=self.user.get_full_name(),
            date=self.course_date,
            status=Printer3DCourse.Status.REGISTERED,
        )
        # Setting this before saving lets `Printer3DCourse.save()` move the card number
        # onto the user it connects the registration to
        registration.card_number = self.card_number
        registration.save()

        base_permission = CoursePermission.objects.get(
            short_name=CoursePermission.DefaultPerms.TAKEN_3D_PRINTER_COURSE
        )
        registration.course_permissions.set({base_permission, *course_permissions})

        self.status = self.Status.APPROVED
        self.save()
        return registration

    def reject(self) -> None:
        self.status = self.Status.REJECTED
        self.save()
