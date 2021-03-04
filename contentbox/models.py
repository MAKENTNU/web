from django.db import models
from django.utils.translation import gettext_lazy as _

from web.multilingual.modelfields import MultiLingualRichTextUploadingField


class ContentBox(models.Model):
    title = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("title"),
    )
    content = MultiLingualRichTextUploadingField(verbose_name=_("content"))

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
        return self.title
