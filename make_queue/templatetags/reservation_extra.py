from django import template
from django.utils import timezone
from django.urls import reverse

register = template.Library()


@register.simple_tag()
def calendar_url_reservation(reservation):
    return reverse('reservation_calendar',
                   kwargs={'year': reservation.start_time.year, 'week': reservation.start_time.isocalendar()[1],
                           'machine_type': reservation.machine.literal, 'pk': reservation.machine.pk})


@register.simple_tag()
def current_calendar_url(machine_type, machine_pk):
    current_time = timezone.now()
    return reverse('reservation_calendar',
                   kwargs={'year': current_time.year, 'week': current_time.isocalendar()[1],
                           'machine_type': machine_type, 'pk': machine_pk})


@register.simple_tag()
def card_color_from_machine_status(machine):
    colors = {
        "F": "green",
        "O": "red",
        "R": "blue",
        "I": "orange",
        "M": "brown"
    }
    return colors[machine.status]


@register.simple_tag()
def is_current_date(date):
    return timezone.now().date() == date


@register.simple_tag()
def get_current_time_of_day():
    return date_to_percentage(timezone.now())


@register.simple_tag()
def date_to_percentage(date):
    return (date.hour / 24 + date.minute / 1440) * 100
