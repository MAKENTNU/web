from django.contrib.auth.models import Permission
from django.db import models
from django.urls import NoReverseMatch
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse
from simple_history.models import HistoricalRecords

from util.auth_utils import perms_to_str
from util.validators import lowercase_slug_validator
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class ContentBox(models.Model):
    url_name = models.CharField(
        max_length=100,
        unique=True,
        validators=[lowercase_slug_validator],
        verbose_name=_("URL name"),
    )
    title = MultiLingualTextField(verbose_name=_("title"))
    content = MultiLingualRichTextUploadingField(verbose_name=_("content"))
    extra_change_permissions = models.ManyToManyField(
        to=Permission,
        blank=True,
        related_name='content_boxes_with_extra_change_perm',
        verbose_name=_("extra change permissions"),
        help_text=_("Extra permissions that are required for editing the content box."),
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    history = HistoricalRecords(m2m_fields=[extra_change_permissions], excluded_fields=['last_modified'])

    class Meta:
        permissions = (
            ('can_upload_image', "Can upload images in CKEditor"),
            ('can_browse_image', "Can browse images in CKEditor"),
            # Internal content boxes should have a permission that is separate from the public content boxes'
            ('change_internal_contentbox', "Can change internal content boxes"),
        )
        verbose_name = "content box"
        verbose_name_plural = "content boxes"

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        # Should update this code if any content box URLs are placed under other subdomains
        all_host_kwargs = [
            {'host': 'main'},
            {'host': 'internal', 'host_args': ['i']},
            {'host': 'docs'},
        ]
        for host_kwargs in all_host_kwargs:
            try:
                return reverse(self.url_name, **host_kwargs)
            except NoReverseMatch:
                pass
        raise NoReverseMatch(f"Unable to find {self._meta.object_name} with url_name '{self.url_name}'")

    @property
    def extra_change_perms_str_tuple(self):
        return perms_to_str(self.extra_change_permissions.all())
