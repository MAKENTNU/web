from datetime import datetime

from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.timesince import timeuntil
from django.utils.translation import gettext_lazy as _

from users.models import User
from util.locale_utils import TIME_STRINGS, get_current_year_and_week, get_year_and_week
from ..models.machine import Machine
from ..models.reservation import Quota, Reservation

register = template.Library()


def _machine_detail_query(year_and_week: tuple[int, int]):
    year, week = year_and_week
    return urlencode({'calendar_year': year, 'calendar_week': week})


@register.simple_tag
def calendar_url_reservation(reservation: Reservation):
    query_string = _machine_detail_query(get_year_and_week(reservation.start_time))
    return f"{reverse('machine_detail', args=[reservation.machine.pk])}?{query_string}"


@register.simple_tag
def current_calendar_url(machine: Machine):
    query_string = _machine_detail_query(get_current_year_and_week())
    return f"{reverse('machine_detail', args=[machine.pk])}?{query_string}"


@register.simple_tag
def calendar_url_timestamp(machine: Machine, time: datetime):
    query_string = _machine_detail_query(get_year_and_week(time))
    return f"{reverse('machine_detail', args=[machine.pk])}?{query_string}"


@register.simple_tag
def numeric_range(start, end, step=1):
    return list(range(start, end, step))


@register.simple_tag
def card_color_from_machine_status(machine: Machine):
    colors = {
        Machine.Status.RESERVED: "blue",
        Machine.Status.AVAILABLE: "green",
        Machine.Status.IN_USE: "orange",
        Machine.Status.OUT_OF_ORDER: "red",
        Machine.Status.MAINTENANCE: "brown",
    }
    return colors[machine.get_status()]


@register.simple_tag
def shorthand_days():
    return [_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun")]


@register.simple_tag
def card_text_from_machine_status(machine: Machine):
    status = machine.get_status_display()
    next_reservation = machine.get_next_reservation()

    # If the machine is free for less than a day, provide the number of hours/minutes until the next reservation.
    if (machine.get_status() == Machine.Status.AVAILABLE
            and next_reservation is not None
            and (next_reservation.start_time - timezone.localtime()).days < 1):
        status = _("{machine_status} for {duration}").format(
            machine_status=status,
            duration=timeuntil(next_reservation.start_time, time_strings=TIME_STRINGS),
        )
    return status


@register.simple_tag
def reservation_denied_message(user: User, machine: Machine):
    if not user.is_authenticated:
        return _("You must be logged in to create reservations.")
    elif not machine.can_user_use(user):
        return machine.machine_type.cannot_use_text
    reservable, status_display = machine.reservable_status_display_tuple()
    if not reservable:
        return _("The machine has status “{status}”.").format(status=status_display)
    elif not Quota.can_create_new_reservation(user, machine.machine_type):
        return _("You have reached the maximum number of future reservations.")
    else:
        return ""


@register.simple_tag
def can_change_reservation(reservation: Reservation, user: User):
    return reservation.can_be_changed_by(user) and (reservation.can_change_start_time() or reservation.can_change_end_time())


@register.simple_tag
def can_delete_reservation(reservation: Reservation, user: User):
    return reservation.can_be_deleted_by(user)


@register.simple_tag
def can_mark_reservation_finished(reservation: Reservation):
    return reservation.start_time < timezone.now() < reservation.end_time


@register.simple_tag
def is_future_reservation(reservation: Reservation):
    return reservation.end_time >= timezone.now()


@register.simple_tag
def get_stream_image_path(status: Machine.Status) -> str:
    status_image_dict = {
        Machine.Status.MAINTENANCE: static('make_queue/img/maintenance.svg'),
        Machine.Status.OUT_OF_ORDER: static('make_queue/img/out_of_order.svg'),
    }
    return status_image_dict.get(status, static('make_queue/img/no_stream.svg'))
