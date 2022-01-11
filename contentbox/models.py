from django.db import models
from django.utils.translation import gettext_lazy as _

from util.validators import lowercase_slug_validator
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class ContentBox(models.Model):
    url_name = models.CharField(
        max_length=100,
        unique=True,
        validators=[lowercase_slug_validator],
        verbose_name=_("URL name"),
    )
    title = MultiLingualTextField(verbose_name=_("Title"))
    content = MultiLingualRichTextUploadingField(verbose_name=_("Content"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        permissions = (
            ('can_upload_image', "Can upload images in CKEditor"),
            ('can_browse_image', "Can browse images in CKEditor"),
        )
        verbose_name = "content box"
        verbose_name_plural = "content boxes"

    def __str__(self):
        return str(self.title)
