from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from util import html_utils
from util.admin_utils import DefaultAdminWidgetsMixin, search_escaped_and_unescaped
from .models import Equipment


class EquipmentAdmin(DefaultAdminWidgetsMixin, SimpleHistoryAdmin):
    list_display = ('title', 'get_image', 'priority', 'last_modified')
    search_fields = ('title', 'description')
    list_editable = ('priority',)

    readonly_fields = ('last_modified',)

    @admin.display(description=_("image"))
    def get_image(self, equipment: Equipment):
        return html_utils.tag_media_img(
            equipment.image.url, url_host_name='main',
            alt_text=_("Image of {equipment}.").format(equipment=equipment.title),
        )

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()


admin.site.register(Equipment, EquipmentAdmin)
