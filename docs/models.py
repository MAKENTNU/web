from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.translation import gettext_lazy as _


class Page(models.Model):
    """Model for each individual documentation page"""
    title = models.CharField(max_length=64, unique=True, verbose_name=_("Title"))

    @property
    def content(self):
        """Finds the current content of the page in the content history"""
        if self.content_history.exists():
            return self.content_history.order_by("changed").last()
        return ""


class Content(models.Model):
    """The content of a documentation page. All versions are kept for editing history."""
    page = models.ForeignKey(Page, models.CASCADE, related_name="content_history", verbose_name=_("Page"))
    changed = models.DateTimeField(verbose_name=_("Time changed"))
    content = RichTextUploadingField(verbose_name=_("Content"))
