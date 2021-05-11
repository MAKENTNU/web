from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from util.admin_utils import TextFieldOverrideMixin
from web.multilingual.admin import MultiLingualFieldAdmin
from .models.course import Printer3DCourse
from .models.models import Machine, MachineType, Quota, Reservation, ReservationRule


class MachineTypeAdmin(MultiLingualFieldAdmin):
    list_display = ('name', 'usage_requirement', 'has_stream', 'get_num_machines', 'priority')
    list_filter = ('usage_requirement', 'has_stream')
    search_fields = ('name', 'cannot_use_text')
    list_editable = ('priority',)
    ordering = ('priority',)

    @admin.display(
        ordering='machines__count',
        description=_("Machines"),
    )
    def get_num_machines(self, machine_type: MachineType):
        return machine_type.machines__count

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(Count('machines'))  # facilitates querying `machines__count`


class MachineAdmin(TextFieldOverrideMixin, admin.ModelAdmin):
    list_display = ('name', 'machine_model', 'machine_type', 'get_location', 'status', 'priority')
    list_filter = ('machine_type', 'machine_model', 'location', 'status')
    search_fields = ('name', 'machine_model', 'machine_type__name', 'location', 'location_url')
    list_editable = ('status', 'priority')
    list_select_related = ('machine_type',)

    @admin.display(
        ordering='location',
        description=_("Location"),
    )
    def get_location(self, machine: Machine):
        return format_html('<a href="{}" target="_blank">{}</a>', machine.location_url, machine.location)

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()


class ReservationAdmin(TextFieldOverrideMixin, admin.ModelAdmin):
    pass


class Printer3DCourseAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'name', 'date', 'status', 'advanced_course')
    list_filter = ('status', 'advanced_course')
    search_fields = ('username', 'user', 'name')
    list_editable = ('status', 'advanced_course')
    ordering = ('date', 'username')


admin.site.register(MachineType, MachineTypeAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(Quota)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(ReservationRule)

admin.site.register(Printer3DCourse, Printer3DCourseAdmin)
