from django.db import models
from django.db.models import F
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from web.multilingual.database import MultiLingualRichTextUploadingField, MultiLingualTextField


class EquipmentQuerySet(models.QuerySet):

    def default_order_by(self):
        return self.order_by(
            F('priority').asc(nulls_last=True),
            Lower('title'),
        )


class Equipment(models.Model):
    title = MultiLingualTextField(
        max_length=100,
        unique=True,
        verbose_name=_('Title'),
    )
    image = models.ImageField(upload_to='equipment', verbose_name=_('Image'))
    description = MultiLingualRichTextUploadingField(verbose_name=_('Description'))
    priority = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Priority"),
        help_text=_("If specified, the equipment is sorted ascending by this value."),
    )

    objects = EquipmentQuerySet.as_manager()

    def __str__(self):
        return str(self.title)
