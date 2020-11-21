from django.contrib import admin
from django.db.models import Count, Q
from django.db.models.functions import Concat, Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from users.admin import get_user_search_fields
from web.multilingual.database import MultiLingualFieldAdmin
from .models.course import Printer3DCourse
from .models.models import Machine, MachineType, MachineUsageRule, Quota, Reservation, ReservationQuerySet, ReservationRule


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


class MachineUsageRuleAdmin(MultiLingualFieldAdmin):
    list_display = ('machine_type',)
    search_fields = ('machine_type__name', 'content')
    ordering = ('machine_type__priority',)
    list_select_related = ('machine_type',)


class QuotaAdmin(admin.ModelAdmin):
    list_display = (
        'get_user', 'all', 'machine_type',
        'diminishing', 'ignore_rules', 'number_of_reservations',
        'get_total_reservations', 'get_active_reservations',
    )
    list_filter = ('machine_type', 'diminishing', 'ignore_rules')
    search_fields = (*get_user_search_fields('user__'), 'machine_type__name')
    list_editable = ('number_of_reservations',)
    ordering = ('user',)
    list_select_related = ('user', 'machine_type')

    autocomplete_fields = ('user',)

    def get_user(self, quota: Quota):
        if quota.all:
            return _("<all users>")
        elif not quota.user:
            return _("<nobody>")
        return quota.user.get_full_name() or quota.user

    get_user.short_description = _("User")
    get_user.admin_order_field = Concat('user__first_name', 'user__last_name')

    def get_total_reservations(self, quota: Quota):
        return quota.num_reservations

    get_total_reservations.short_description = _("Total registered reservations")
    get_total_reservations.admin_order_field = 'num_reservations'

    def get_active_reservations(self, quota: Quota):
        return quota.num_active_reservations

    get_active_reservations.short_description = _("Active reservations")
    get_active_reservations.admin_order_field = 'num_active_reservations'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            num_reservations=Count('reservations'),
            num_active_reservations=Count('reservations', filter=Q(reservations__end_time__gte=timezone.now())),
        )


class ReservationAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'machine', 'start_time', 'get_duration', 'end_time', 'get_event', 'special_text', 'comment', 'get_quota')
    list_filter = ('machine', 'machine__machine_type', 'machine__machine_model', 'special')
    search_fields = (
        *get_user_search_fields('user__'),
        'machine__name', 'machine__machine_type__name', 'machine__machine_model',
        'event__event__title',
        'special_text', 'comment',
    )
    ordering = ('-start_time',)

    autocomplete_fields = ('user',)
    raw_id_fields = ('event', 'quota')

    def get_user(self, reservation: Reservation):
        return reservation.user.get_full_name() or reservation.user

    get_user.short_description = _("User")
    get_user.admin_order_field = Concat('user__first_name', 'user__last_name')

    def get_duration(self, reservation: Reservation):
        return reservation.duration

    get_duration.short_description = _("Duration")
    get_duration.admin_order_field = 'duration'

    def get_event(self, reservation: Reservation):
        event_timeplace = reservation.event
        if not event_timeplace:
            return None
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            reverse('admin:news_timeplace_change', args=[event_timeplace.pk]),
            event_timeplace,
        )

    get_event.short_description = _("Event")
    get_event.admin_order_field = 'event'

    def get_quota(self, reservation: Reservation):
        connected_quota = reservation.quota
        if not connected_quota:
            return None
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            reverse('admin:make_queue_quota_change', args=[connected_quota.pk]),
            connected_quota,
        )

    get_quota.short_description = _("Quota")
    get_quota.admin_order_field = 'quota'

    def get_queryset(self, request):
        qs: ReservationQuerySet = super().get_queryset(request)
        qs = qs.select_related('user', 'machine__machine_type', 'quota').prefetch_related('event__event')
        return qs.annotate_durations()


class ReservationRuleAdmin(admin.ModelAdmin):
    list_display = (
        'machine_type',
        'start_time', 'end_time',
        'days_changed', 'get_start_days',
        'max_hours', 'max_inside_border_crossed',
    )
    list_filter = ('machine_type',)
    search_fields = ('machine_type__name',)
    ordering = ('machine_type',)
    list_select_related = ('machine_type',)

    def get_start_days(self, reservation_rule: ReservationRule):
        return str(reservation_rule.start_days)

    get_start_days.short_description = _("Start days for rule periods")


class Printer3DCourseAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'date', 'get_card_number', 'status')
    list_filter = ('status',)
    search_fields = (
        *get_user_search_fields('user__'),
        'username', 'name',
        'user__card_number', '_card_number',
    )
    list_editable = ('status',)
    ordering = ('-date',)
    list_select_related = ('user',)

    autocomplete_fields = ('user',)

    def get_user(self, course: Printer3DCourse):
        return course.get_user_display_name()

    get_user.short_description = _("User")
    get_user.admin_order_field = Concat('user__first_name', 'user__last_name')

    def get_card_number(self, course: Printer3DCourse):
        return course.card_number

    get_card_number.short_description = _("Card number")
    get_card_number.admin_order_field = Concat('user__card_number', '_card_number')


admin.site.register(MachineType, MachineTypeAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(MachineUsageRule, MachineUsageRuleAdmin)
admin.site.register(Quota, QuotaAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(ReservationRule, ReservationRuleAdmin)

admin.site.register(Printer3DCourse, Printer3DCourseAdmin)
