from django import template

from news.models import Event, TimePlace
from users.models import User

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
