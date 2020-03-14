from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from web.multilingual.database import MultiLingualTextField


class AnnouncementManager(models.Manager):

    def valid(self):
        """Finds all announcements that are currently valid"""
        return self.filter(display_from__lte=timezone.localtime().now()).filter(
            Q(display_to__isnull=True) | Q(display_to__gt=timezone.localtime().now()))

    def valid_site_wide(self):
        """Finds all currently valid announcements that should be displayed site-wide"""
        return self.valid().filter(site_wide=True)

    def valid_non_site_wide(self):
        """Finds all currently valid announcements that should not be displayed site-wide"""
        return self.valid().filter(site_wide=False)


class Announcement(models.Model):
    """
    Model for general announcements. All announcements are time-based, but can be shown for an indefinite time period if
    there is no end time given. An announcement may also link to another page with more information.
    """
    objects = AnnouncementManager()

    class AnnouncementType(models.TextChoices):
        INFO = "I", _("Information")
        WARNING = "W", _("Warning")
        ERROR = "E", _("Error")

    classification = models.CharField(max_length=1, choices=AnnouncementType.choices, default=AnnouncementType.INFO,
                                      verbose_name=_("Type"))
    site_wide = models.BooleanField(verbose_name=_("Site-wide"))
    content = MultiLingualTextField(max_length=256, verbose_name=_("Content"))
    link = models.CharField(max_length=2048, verbose_name=_("Link"), blank=True, null=True)
    display_from = models.DateTimeField(default=timezone.localtime().now())
    display_to = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_classification_display()}: {self.content}"

    def is_valid(self):
        """Checks if the given reservation is currently valid"""
        return self.display_from <= timezone.localtime() and (
                    self.display_to is None or self.display_to > timezone.localtime())
