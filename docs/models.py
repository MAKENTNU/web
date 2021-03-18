from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User
from .validators import page_title_validator


class Page(models.Model):
    """Model for each individual documentation page"""

    title = models.CharField(max_length=64, unique=True, verbose_name=_("Title"), validators=[page_title_validator])
    created_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    current_content = models.ForeignKey(
        to="Content",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="in_use",
    )

    def __str__(self):
        return self.title


class Content(models.Model):
    """The content of a documentation page. All versions are kept for editing history."""

    page = models.ForeignKey(
        to=Page,
        on_delete=models.CASCADE,
        related_name="content_history",
        verbose_name=_("Page"),
    )
    changed = models.DateTimeField(verbose_name=_("Time changed"))
    content = RichTextUploadingField(verbose_name=_("Content"))
    made_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Made by"),
    )
