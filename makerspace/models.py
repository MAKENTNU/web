from django.db import models

from web.multilingual.database import MultiLingualTextField, MultiLingualRichTextUploadingField


class Tool(models.Model):
    title = MultiLingualTextField(
        max_length=100,
        verbose_name=('Title'),
    )
    image = models.ImageField(verbose_name=('Image'), blank=True, )
    content = MultiLingualRichTextUploadingField()


class Makerspace(models.Model):
    title = MultiLingualTextField(
        max_length=100,
        verbose_name=('Title'),
    )
    image = models.ImageField(verbose_name=('Image'), blank=True, )
    content = MultiLingualRichTextUploadingField()








