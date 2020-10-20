from django.db import models

from django.utils.translation import gettext_lazy as _

from web.multilingual.database import MultiLingualRichTextUploadingField, MultiLingualTextField

from django.core.validators import RegexValidator


class Category(models.Model):
    name = models.CharField(
        max_length=200,
    )

    def __str__(self):
        return str(self.name)


class Question(models.Model):
    title = MultiLingualTextField(
        max_length=255,
        unique=True,
        verbose_name=_('Question'),
    )

    answer = MultiLingualRichTextUploadingField(
        verbose_name=_('Answer'),
    )

    categories = models.ManyToManyField(
        to=Category,
        related_name='questions',
    )

    def __str__(self):
        return str(self.title)

