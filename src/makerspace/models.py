from django.db import models
from django.db.models import F
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse
from simple_history.models import HistoricalRecords

from util.modelfields import CompressedImageField
from util.storage import OverwriteStorage, UploadToUtils
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class EquipmentQuerySet(models.QuerySet):

    def default_order_by(self) -> 'EquipmentQuerySet[Equipment]':
        return self.order_by(
            F('priority').asc(nulls_last=True),
            Lower('title'),
        )


class Equipment(models.Model):
    title = MultiLingualTextField(unique=True, verbose_name=_("title"))
    description = MultiLingualRichTextUploadingField(verbose_name=_("description"))
    image = CompressedImageField(upload_to=UploadToUtils.get_pk_prefixed_filename_func('equipment'),
                                 max_length=200, storage=OverwriteStorage(), verbose_name=_("image"))
    priority = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("priority"),
        help_text=_("If specified, the equipment is sorted ascending by this value."),
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    objects = EquipmentQuerySet.as_manager()
    history = HistoricalRecords(excluded_fields=['priority', 'last_modified'])

    class Meta:
        verbose_name = _("equipment")
        verbose_name_plural = _("equipment")

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('equipment_detail', args=[self.pk])
