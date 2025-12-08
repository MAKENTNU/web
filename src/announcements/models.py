from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from web.modelfields import URLTextField
from web.multilingual.modelfields import MultiLingualTextField


class AnnouncementQuerySet(models.QuerySet):
    def shown(self) -> "AnnouncementQuerySet[Announcement]":
        """Returns a ``QuerySet`` with only the announcements that are currently shown."""
        now = timezone.localtime()
        return self.filter(
            Q(display_from__lte=now)
            & (Q(display_to__isnull=True) | Q(display_to__gt=now))
        )

    def not_shown(self) -> "AnnouncementQuerySet[Announcement]":
        """Returns a ``QuerySet`` with only the announcements that are currently not shown."""
        now = timezone.localtime()
        return self.filter(
            Q(display_from__lte=now) & Q(display_to__lte=now) | Q(display_from__gt=now)
        )

    def site_wide(self) -> "AnnouncementQuerySet[Announcement]":
        """Returns a ``QuerySet`` with only the announcements that should be displayed site-wide."""
        return self.filter(site_wide=True)

    def non_site_wide(self) -> "AnnouncementQuerySet[Announcement]":
        """Returns a ``QuerySet`` with only the announcements that should not be displayed site-wide."""
        return self.filter(site_wide=False)


class Announcement(models.Model):
    """
    Model for general announcements. All announcements are time-based, but can be shown for an indefinite time period if
    there is no end time given. An announcement may also link to another page with more information.
    """

    class Type(models.TextChoices):
        INFO = "I", _("Information")
        WARNING = "W", _("Warning")
        CRITICAL = "C", _("Critical")

    classification = models.CharField(
        choices=Type.choices, max_length=1, default=Type.INFO, verbose_name=_("type")
    )
    site_wide = models.BooleanField(
        verbose_name=_("site-wide"),
        help_text=_(
            "If selected, the announcement will be shown on all pages, otherwise it is"
            " only shown on the front page."
        ),
    )
    content = MultiLingualTextField(verbose_name=_("content"))
    link = URLTextField(
        blank=True,
        verbose_name=_("link"),
        help_text=_("An optional link to an information page."),
    )
    display_from = models.DateTimeField(
        default=timezone.localtime,
        verbose_name=_("display from"),
        help_text=_("The date from which the announcement will be shown."),
    )
    display_to = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("display to"),
        help_text=_(
            "The announcement will be shown until this date. If none is given, it is"
            " shown indefinitely."
        ),
    )

    objects = AnnouncementQuerySet.as_manager()

    def __str__(self):
        return f"{self.get_classification_display()}: {self.content}"

    def is_shown(self):
        """Checks if the given reservation is currently shown."""
        return self.display_from <= timezone.localtime() and (
            self.display_to is None or self.display_to > timezone.localtime()
        )
