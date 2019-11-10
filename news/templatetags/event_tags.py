from django import template

from news.models import Event, EventTicket

register = template.Library()


@register.simple_tag
def is_registered(event, user):
    tickets = EventTicket.objects.filter(user=user, active=True)
    if isinstance(event, Event):
        return tickets.filter(event=event).exists()
    else:
        return tickets.filter(timeplace=event).exists()
