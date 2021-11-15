from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from util import html_utils
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Equipment


class EquipmentAdmin(MultiLingualFieldAdmin):
    list_display = ('title', 'get_image', 'priority', 'last_modified')
    search_fields = ('title', 'description')
    list_editable = ('priority',)
    readonly_fields = ('last_modified',)

    @admin.display(description=_("Image"))
    def get_image(self, equipment: Equipment):
        return html_utils.tag_media_img(
            equipment.image.url, url_host_name='main',
            alt_text=_("Image of {equipment}.").format(equipment=equipment.title),
        )

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()


admin.site.register(Equipment, EquipmentAdmin)
