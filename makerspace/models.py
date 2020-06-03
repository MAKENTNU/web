from django.db import models
from web.multilingual.database import MultiLingualTextField, MultiLingualRichTextUploadingField
from django.utils.translation import gettext_lazy as _


class Tool(models.Model):
    """ Object model  to add description to tools at makerspace/tools """
    title = MultiLingualTextField(
        max_length=100,
        unique=True,
        verbose_name=_('Title'),
    )
    image = models.ImageField(upload_to='tools', verbose_name=_('Image'))
    description = MultiLingualRichTextUploadingField(verbose_name=_('Description'))

