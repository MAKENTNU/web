from django.db import models
from django.utils.translation import gettext_lazy as _

from web.multilingual.database import MultiLingualRichTextUploadingField, MultiLingualTextField


class Equipment(models.Model):
    title = MultiLingualTextField(
        max_length=100,
        unique=True,
        verbose_name=_('Title'),
    )
    image = models.ImageField(upload_to='equipment', verbose_name=_('Image'))
    description = MultiLingualRichTextUploadingField(verbose_name=_('Description'))

    def __str__(self):
        return str(self.title)
