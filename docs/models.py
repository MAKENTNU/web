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
                                     message=_("Only numbers, letters, spaces, parentheses and colons are allowed."))

    title = models.CharField(max_length=64, unique=True, verbose_name=_("Title"), validators=[TITLE_VALIDATOR])
    created_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doc_pages_created',
    )
    current_content = models.OneToOneField(
        to="Content",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        # Can be used as a boolean field by `Content`
        related_name='is_currently_on_page',
    )

    def __str__(self):
        return self.title


class Content(models.Model):
    """The content of a documentation page. All versions are kept for editing history."""
    page = models.ForeignKey(
        to=Page,
        on_delete=models.CASCADE,
        related_name='content_history',
        verbose_name=_("Page"),
    )
    changed = models.DateTimeField(verbose_name=_("Time changed"))
    content = RichTextUploadingField(verbose_name=_("Content"))
    made_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doc_page_contents_created',
        verbose_name=_("Made by"),
    )
