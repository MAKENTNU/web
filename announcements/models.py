from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Announcement(models.Model):
    """
    Model for general announcements. All announcements are time-based, but can be shown for an indefinite time period if
    there is no end time given. An announcement may also link to another page with more information.
    """
    class AnnouncementType(models.TextChoices):
        INFO = "I", _("Information")
        WARNING = "W", _("Warning")
        SIGNIFICANT = "E", _("Error")

    classification = models.CharField(max_length=1, choices=AnnouncementType.choices, default=AnnouncementType.INFO,
                                      verbose_name=_("Type"))
    site_wide = models.BooleanField(verbose_name=_("Site-wide"))
    content = models.CharField(max_length=256, verbose_name=_("Content"))
    link = models.CharField(max_length=2048, verbose_name=_("Link"), blank=True, null=True)
    display_from = models.DateTimeField(default=timezone.localtime().now())
    display_to = models.DateTimeField(blank=True, null=True)
