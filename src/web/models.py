from django.db import models
from django.utils.translation import gettext_lazy as _


class PageView(models.Model):
    path = models.CharField(max_length=255, unique=True, verbose_name=_("path"))
    count = models.PositiveIntegerField(default=0, verbose_name=_("count"))
    last_visited = models.DateTimeField(auto_now=True, verbose_name=_("last visited"))

    class Meta:
        ordering = ["-count"]
        verbose_name = _("page view")
        verbose_name_plural = _("page views")

    def __str__(self):
        return f"{self.path} ({self.count})"


class Visitor(models.Model):
    identifier = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name=_("identifier"),
    )
    first_seen = models.DateTimeField(auto_now_add=True, verbose_name=_("first seen"))
    last_seen = models.DateTimeField(auto_now=True, verbose_name=_("last seen"))

    class Meta:
        verbose_name = _("visitor")
        verbose_name_plural = _("visitors")

    def __str__(self):
        return self.identifier
