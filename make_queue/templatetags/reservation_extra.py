from django import template
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timeuntil
from django.utils.translation import gettext_lazy as _

from make_queue.util.time import date_to_local, get_day_name
from ..models.models import Machine

register = template.Library()


@register.simple_tag()
def calendar_url_reservation(reservation):
    return reverse('reservation_calendar',
                   kwargs={'year': reservation.start_time.year, 'week': reservation.start_time.isocalendar()[1],
                           'machine': reservation.machine})


@register.simple_tag()
def current_calendar_url(machine):
    current_time = timezone.localtime(timezone.now())
    return reverse('reservation_calendar',
                   kwargs={'year': current_time.year, 'week': current_time.isocalendar()[1], 'machine': machine})


@register.simple_tag()
def calendar_url_timestamp(machine, time):
    return reverse("reservation_calendar",
                   kwargs={"year": time.year, "week": time.isocalendar()[1], "machine": machine})


@register.simple_tag()
def numeric_range(start, end, step=1):
    return list(range(start, end, step))


@register.simple_tag()
def card_color_from_machine_status(machine):
    colors = {
        Machine.Status.RESERVED: "blue",
        Machine.Status.AVAILABLE: "green",
        Machine.Status.IN_USE: "orange",
        Machine.Status.OUT_OF_ORDER: "red",
        Machine.Status.MAINTENANCE: "brown",
    }
    return colors[machine.get_status()]


@register.simple_tag()
def is_current_date(date):
    return timezone.localtime(timezone.now()).date() == date


@register.simple_tag()
def shorthand_days():
    return [_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun")]


@register.simple_tag()
def card_text_from_machine_status(machine):
    status = machine.get_status_display()
    next_reservation = machine.get_next_reservation()

    # If the machine is free for less than a day, provide the number of hours/minutes until the next reservation.
    if (machine.get_status() == Machine.Status.AVAILABLE
            and next_reservation is not None
            and (next_reservation.start_time - timezone.now()).days < 1):
        # Uses old format scheme due to gettext not having automatic detection of translations in f-strings
        status = "{:} {:} {:}".format(status, _('for'), timeuntil(next_reservation.start_time))
    return status


@register.simple_tag()
def get_current_time_of_day():
    return date_to_percentage(timezone.localtime(timezone.now()))


@register.simple_tag()
def date_to_percentage(date):
    try:
        date = date_to_local(date)
    except ValueError:
        pass
    return (date.hour / 24 + date.minute / (24 * 60)) * 100


@register.simple_tag()
def can_use_machine(machine, user):
    return machine.can_user_use(user)


@register.simple_tag()
def get_machine_cannot_use_text(machine):
    return machine.machine_type.cannot_use_text


@register.simple_tag()
def invert(expression):
    return ["false", "true"][not expression]


@register.simple_tag()
def rule_period_start_text(period, locale):
    return get_day_name(int(period.start_time // 1), locale) + " " + period.rule.start_time.strftime("%H:%M")


@register.simple_tag()
def rule_period_end_text(period, locale):
    return get_day_name(int(period.end_time // 1) % 7, locale) + " " + period.rule.end_time.strftime("%H:%M")


@register.simple_tag()
def can_change_reservation(reservation, user):
    return reservation.can_change(user) or reservation.can_change_end_time(user)


@register.simple_tag()
def can_change_reservation_end_time(reservation, user):
    return reservation.can_change_end_time(user)


@register.simple_tag()
def can_delete_reservation(reservation, user):
    return reservation.can_delete(user)


@register.simple_tag()
def can_mark_reservation_as_finished(reservation):
    return reservation.start_time < timezone.now() < reservation.end_time


@register.simple_tag()
def is_future_reservation(reservation):
    return reservation.end_time >= timezone.now()


@register.simple_tag()
def sanitize_stream_name(machine):
    values = (
        (" ", "-"),
        ("ö", "o"),
    )
    name = machine.name
    for original, new in values:
        name = name.replace(original, new)
    return name
