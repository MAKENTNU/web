from django import template

from users.models import User
from ..models import Event, TimePlace

register = template.Library()


@register.simple_tag
def get_ticket(event_or_timeplace: Event | TimePlace, user: User):
    if not user.is_authenticated:
        return None
    tickets = user.event_tickets.filter(active=True)
    if isinstance(event_or_timeplace, Event):
        return tickets.filter(event=event_or_timeplace).first()
    else:
        return tickets.filter(timeplace=event_or_timeplace).first()
