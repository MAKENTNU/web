from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from util.admin_utils import DefaultAdminWidgetsMixin, UserSearchFieldsMixin, search_escaped_and_unescaped
from util.templatetags.html_tags import anchor_tag
from .models.course import Printer3DCourse
from .models.machine import Machine, MachineType, MachineUsageRule
from .models.reservation import Quota, Reservation, ReservationRule


class MachineTypeAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ('name', 'usage_requirement', 'has_stream', 'get_num_machines', 'priority')
    list_filter = ('usage_requirement', 'has_stream')
    search_fields = ('name', 'cannot_use_text')
    list_editable = ('priority',)
    ordering = ('priority',)

    @admin.display(
        ordering='machines__count',
        description=_("machines"),
    )
    def get_num_machines(self, machine_type: MachineType):
        return machine_type.machines__count

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(Count('machines'))  # facilitates querying `machines__count`

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


class MachineAdmin(DefaultAdminWidgetsMixin, SimpleHistoryAdmin):
    list_display = ('name', 'machine_model', 'machine_type', 'get_location', 'internal', 'status', 'priority', 'last_modified')
    list_filter = ('machine_type', 'machine_model', 'location', 'status')
    search_fields = ('name', 'stream_name', 'machine_model', 'machine_type__name', 'location', 'location_url')
    list_editable = ('status', 'priority', 'internal')
    list_select_related = ('machine_type',)

    readonly_fields = ('last_modified',)

    @admin.display(
        ordering='location',
        description=_("location"),
    )
    def get_location(self, machine: Machine):
        return anchor_tag(machine.location_url, machine.location)

    def get_queryset(self, request):
        return super().get_queryset(request).default_order_by()


class MachineUsageRuleAdmin(DefaultAdminWidgetsMixin, SimpleHistoryAdmin):
    list_display = ('machine_type', 'last_modified')
    list_select_related = ('machine_type',)

    readonly_fields = ('last_modified',)


class ReservationAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    pass


class ReservationRuleAdmin(admin.ModelAdmin):
    list_display = (
        'machine_type',
        'start_time', 'days_changed', 'end_time',
        'start_days', 'max_hours', 'max_inside_border_crossed',
        'last_modified',
    )
    ordering = ('machine_type',)
    list_select_related = ('machine_type',)

    readonly_fields = ('last_modified',)


class Printer3DCourseAdmin(DefaultAdminWidgetsMixin, UserSearchFieldsMixin, admin.ModelAdmin):
    list_display = ('username', 'user', 'name', 'date', 'status', 'raise3d_course', 'sla_course', 'last_modified')
    list_filter = ('status', 'raise3d_course', 'sla_course')
    search_fields = (
        'username', 'name',
        'user__card_number', '_card_number',
        # The user search fields are appended in `UserSearchFieldsMixin`
    )
    user_lookup, name_for_full_name_lookup = 'user__', 'user_full_name'
    list_editable = ('status', 'raise3d_course', 'sla_course')
    ordering = ('date', 'username')
    list_select_related = ('user',)

    readonly_fields = ('last_modified',)


admin.site.register(MachineType, MachineTypeAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(MachineUsageRule, MachineUsageRuleAdmin)
admin.site.register(Quota)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(ReservationRule, ReservationRuleAdmin)

admin.site.register(Printer3DCourse, Printer3DCourseAdmin)
