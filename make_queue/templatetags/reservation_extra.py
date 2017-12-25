from django import template
from django.utils import timezone
from django.urls import reverse

register = template.Library()


@register.simple_tag()
def can_delete_reservation(reservation):
    return timezone.now() < reservation.end_time


@register.simple_tag()
def calendar_url_reservation(reservation):
    return reverse('reservation_calendar',
                   kwargs={'year': reservation.start_time.year, 'week': reservation.start_time.isocalendar()[1],
                           'machine_type': reservation.machine.literal})


@register.simple_tag()
def current_calendar_url():
    current_time = timezone.now()
    return reverse('reservation_calendar',
                   kwargs={'year': current_time.year, 'week': current_time.isocalendar()[1]})
