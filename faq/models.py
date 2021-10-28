from django.db import models
from django.utils.translation import gettext_lazy as _

from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class Category(models.Model):
    name = MultiLingualTextField(unique=True, verbose_name=_("Category"))

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return str(self.name)


class Question(models.Model):
    title = MultiLingualTextField(unique=True, verbose_name=_("Question"))
    answer = MultiLingualRichTextUploadingField(verbose_name=_("Answer"))
    categories = models.ManyToManyField(
        to=Category,
        related_name='questions',
        verbose_name=_("Categories"),
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return str(self.title)
