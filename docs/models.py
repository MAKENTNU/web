from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse

from users.models import User
from .validators import page_title_validator


MAIN_PAGE_TITLE = "Documentation"


class Page(models.Model):
    """Model for each individual documentation page."""
    title = models.CharField(max_length=64, unique=True, verbose_name=_("title"), validators=[page_title_validator])
    created_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doc_pages_created',
    )
    current_content = models.OneToOneField(
        to='Content',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='page_currently_on',
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('page_detail', args=[self.pk], host='docs')

    @classmethod
    def get_main_page(cls) -> 'Page':
        main_page, _created = Page.objects.get_or_create(title=MAIN_PAGE_TITLE)
        return main_page


class Content(models.Model):
    """The content of a documentation page. All versions are kept for editing history."""
    page = models.ForeignKey(
        to=Page,
        on_delete=models.CASCADE,
        related_name='content_history',
        verbose_name=_("page"),
    )
    content = RichTextUploadingField(verbose_name=_("content"))
    made_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doc_page_contents_created',
        verbose_name=_("made by"),
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    def get_absolute_url(self):
        return reverse('page_content_detail', args=[self.page.pk, self.pk], host='docs')
