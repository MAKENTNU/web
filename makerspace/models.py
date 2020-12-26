from django.db import models
from django.db.models import F
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from util.storage import OverwriteStorage, UploadToUtils
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField


class EquipmentQuerySet(models.QuerySet):

    def default_order_by(self):
        return self.order_by(
            F('priority').asc(nulls_last=True),
            Lower('title'),
        )


class Equipment(models.Model):
    title = MultiLingualTextField(unique=True, verbose_name=_("Title"))
    description = MultiLingualRichTextUploadingField(verbose_name=_("Description"))
    image = models.ImageField(upload_to=UploadToUtils.get_pk_prefixed_filename_func('equipment'),
                              max_length=200, storage=OverwriteStorage(), verbose_name=_("Image"))
    priority = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Priority"),
        help_text=_("If specified, the equipment is sorted ascending by this value."),
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    objects = EquipmentQuerySet.as_manager()

    def __str__(self):
        return str(self.title)
