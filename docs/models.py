from ckeditor_uploader.fields import RichTextUploadingField
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


class Page(models.Model):
    """Model for each individual documentation page"""
    title_regex = r"^[0-9A-Za-z ():]+$"
    title_validator = RegexValidator(regex=title_regex,
                                     message=_("Only numbers, letters, space, parenthesises and colon are allowed"))
    title = models.CharField(max_length=64, unique=True, verbose_name=_("Title"), validators=[title_validator])
    created_by = models.ForeignKey(User, models.SET_NULL, null=True, blank=True)
    current_content = models.ForeignKey("Content", models.SET_NULL, null=True, blank=True, related_name="in_use")

    def __str__(self):
        return self.title


class Content(models.Model):
    """The content of a documentation page. All versions are kept for editing history."""
    page = models.ForeignKey(Page, models.CASCADE, related_name="content_history", verbose_name=_("Page"))
    changed = models.DateTimeField(verbose_name=_("Time changed"))
    content = RichTextUploadingField(verbose_name=_("Content"))
    made_by = models.ForeignKey(User, models.SET_NULL, verbose_name=_("Made by"), null=True, blank=True)
