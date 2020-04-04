from django import template

from ..models import Event, EventTicket

register = template.Library()


@register.simple_tag
def get_ticket(event, user):
    if not user.is_authenticated:
        return None
    tickets = EventTicket.objects.filter(user=user, active=True)
    if isinstance(event, Event):
        return tickets.filter(event=event).first()
    else:
        return tickets.filter(timeplace=event).first()
