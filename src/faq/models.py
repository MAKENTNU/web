from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class CategoryQuerySet(models.QuerySet):

    def prefetch_questions_and_default_order_by(self, *, questions_attr_name: str) -> 'CategoryQuerySet[Category]':
        """
        Returns a ``QuerySet`` where all the categories' questions have been prefetched
        and can be accessed through the attribute with the same name as ``questions_attr_name``.
        """
        return self.order_by('name').prefetch_related(
            Prefetch('questions', queryset=Question.objects.order_by('title'), to_attr=questions_attr_name)
        )


class Category(models.Model):
    name = MultiLingualTextField(unique=True, verbose_name=_("category"))

    objects = CategoryQuerySet.as_manager()

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
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    history = HistoricalRecords(m2m_fields=[categories], excluded_fields=['last_modified'])

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")

    def __str__(self):
        return str(self.title)
