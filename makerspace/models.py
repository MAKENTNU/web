from django.db import models
from web.multilingual.database import MultiLingualTextField, MultiLingualRichTextUploadingField
from django.utils.translation import gettext_lazy as _


class Tool(models.Model):
    """ Object model  to add description to tools at makerspace/tools """
    title = MultiLingualTextField(
        max_length=100,
        verbose_name=_('Title'),
    )
    image = models.ImageField(verbose_name=_('Image'), blank=True, )
    content = MultiLingualRichTextUploadingField()


class Makerspace(models.Model):
    """ Object model  to add description at makentnu/makerspace  """
    title = MultiLingualTextField(
        max_length=100,
        verbose_name=_('Title'),
    )
    content = MultiLingualRichTextUploadingField()
