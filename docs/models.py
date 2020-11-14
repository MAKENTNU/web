from ckeditor_uploader.fields import RichTextUploadingField
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


MAIN_PAGE_TITLE = "Documentation"


class Page(models.Model):
    """Model for each individual documentation page"""
    TITLE_REGEX = r"^[0-9A-Za-z ():]+$"
    TITLE_VALIDATOR = RegexValidator(regex=TITLE_REGEX,
                                     message=_("Only numbers, letters, space, parenthesises and colon are allowed"))

    title = models.CharField(max_length=64, unique=True, verbose_name=_("Title"), validators=[TITLE_VALIDATOR])
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
