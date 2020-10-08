from django.contrib import admin
from django.forms import Select
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models.course import Printer3DCourse
from .models.models import Machine, Quota, Reservation, ReservationRule


class MachineTypeOverride(admin.ModelAdmin):
    """
    Class used to override the Fomantic UI select widget of the machine type field.
    """

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "machine_type":
            kwargs["widget"] = Select()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class MachineAdmin(MachineTypeOverride):
    list_display = ('name', 'machine_model', 'machine_type', 'get_location', 'status', 'priority')
    list_filter = ('machine_type', 'machine_model', 'location', 'status')
    search_fields = ('name', 'machine_model', 'location', 'location_url')
    list_editable = ('status', 'priority')

    def get_location(self, machine: Machine):
        return format_html('<a href="{}" target="_blank">{}</a>', machine.location_url, machine.location)

    get_location.short_description = _("Location")
    get_location.admin_order_field = 'location'


admin.site.register(ReservationRule, MachineTypeOverride)
admin.site.register(Reservation)
admin.site.register(Machine, MachineAdmin)
admin.site.register(Quota, MachineTypeOverride)
admin.site.register(Printer3DCourse)
