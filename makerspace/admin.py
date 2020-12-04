from django.contrib import admin
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from util import html_utils
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Equipment


class EquipmentAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'get_image', 'priority')
    search_fields = ('title', 'description')
    list_editable = ('priority',)
    ordering = ('priority', Lower('title'))

    def get_image(self, equipment: Equipment):
        return html_utils.tag_media_img(
            equipment.image.url, url_host_name='main',
            alt_text=_("Image of {equipment}.").format(equipment=equipment.title),
        )

    get_image.short_description = _("Image")


admin.site.register(Equipment, EquipmentAdmin)
