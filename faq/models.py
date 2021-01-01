from django.db import models
from django.utils.translation import gettext_lazy as _

from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class Category(models.Model):
    name = MultiLingualTextField(unique=True, verbose_name=_("category"))

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return str(self.name)


class Question(models.Model):
    title = MultiLingualTextField(unique=True, verbose_name=_("question"))
    answer = MultiLingualRichTextUploadingField(verbose_name=_("answer"))
    categories = models.ManyToManyField(
        to=Category,
        related_name='questions',
        verbose_name=_("categories"),
    )

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")

    def __str__(self):
        return str(self.title)
