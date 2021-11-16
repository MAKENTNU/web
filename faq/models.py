from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class CategoryQuerySet(models.QuerySet):

    def prefetch_questions_and_default_order_by(self, *, questions_attr_name: str):
        """
        Returns a ``QuerySet`` where all the categories' questions have been prefetched
        and can be accessed through the attribute with the same name as ``questions_attr_name``.
        """
        return self.order_by('name').prefetch_related(
            Prefetch('questions', queryset=Question.objects.order_by('title'), to_attr=questions_attr_name)
        )


class Category(models.Model):
    name = MultiLingualTextField(unique=True, verbose_name=_("Category"))

    objects = CategoryQuerySet.as_manager()

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
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return str(self.title)
