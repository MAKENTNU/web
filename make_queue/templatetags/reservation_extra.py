from django import template
from django.utils import timezone
from django.urls import reverse

from make_queue.util.time import date_to_local

register = template.Library()


@register.simple_tag()
def calendar_url_reservation(reservation):
    return reverse('reservation_calendar',
                   kwargs={'year': reservation.start_time.year, 'week': reservation.start_time.isocalendar()[1],
                           'machine': reservation.get_machine()})


@register.simple_tag()
def current_calendar_url(machine):
    current_time = timezone.localtime(timezone.now())
    return reverse('reservation_calendar',
                   kwargs={'year': current_time.year, 'week': current_time.isocalendar()[1], 'machine': machine})


@register.simple_tag()
def numeric_range(start, end, step=1):
    return list(range(start, end, step))


@register.simple_tag()
def card_color_from_machine_status(machine):
    colors = {
        "F": "green",
        "O": "red",
        "R": "blue",
        "I": "orange",
        "M": "brown"
    }
    return colors[machine.get_status()]


@register.simple_tag()
def is_current_date(date):
    return timezone.localtime(timezone.now()).date() == date


@register.simple_tag()
def get_current_time_of_day():
    return date_to_percentage(timezone.localtime(timezone.now()))


@register.simple_tag()
def date_to_percentage(date):
    try:
        date = date_to_local(date)
    except ValueError:
        pass
    return (date.hour / 24 + date.minute / 1440) * 100


@register.simple_tag()
def can_use_machine(machine, user):
    return machine.can_user_use(user)


@register.simple_tag()
def get_machine_cannot_use_text(machine):
    return machine.cannot_use_text


@register.simple_tag()
def invert(expression):
    return ["false", "true"][not expression]
