from django.contrib import admin
from django.db.models import Count
from django.db.models.functions import Lower
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from web.multilingual.admin import MultiLingualFieldAdmin
from .models.course import Printer3DCourse
from .models.models import Machine, MachineType, Quota, Reservation, ReservationRule


class MachineTypeAdmin(MultiLingualFieldAdmin):
    list_display = ('name', 'usage_requirement', 'has_stream', 'get_num_machines', 'priority')
    list_filter = ('usage_requirement', 'has_stream')
    search_fields = ('name', 'cannot_use_text')
    list_editable = ('priority',)
    ordering = ('priority',)

    def get_num_machines(self, machine_type: MachineType):
        return machine_type.machines__count

    get_num_machines.short_description = _("Machines")
    get_num_machines.admin_order_field = 'machines__count'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(Count('machines'))  # facilitates querying `machines__count`


class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'machine_model', 'machine_type', 'get_location', 'status', 'priority')
    list_filter = ('machine_type', 'machine_model', 'location', 'status')
    search_fields = ('name', 'machine_model', 'machine_type__name', 'location', 'location_url')
    list_editable = ('status', 'priority')
    ordering = ('machine_type__priority', 'priority', Lower('name'))
    list_select_related = ('machine_type',)

    def get_location(self, machine: Machine):
        return format_html('<a href="{}" target="_blank">{}</a>', machine.location_url, machine.location)

    get_location.short_description = _("Location")
    get_location.admin_order_field = 'location'


admin.site.register(MachineType, MachineTypeAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(Quota)
admin.site.register(Reservation)
admin.site.register(ReservationRule)

admin.site.register(Printer3DCourse)
