from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def color(val):
    return 'yellow' if val else 'grey'


@register.filter
def past(timeplaces):
    return timeplaces.filter(end_time__lte=timezone.now()).order_by("-end_time")


@register.filter
def future(timeplaces):
    return timeplaces.filter(end_time__gt=timezone.now())
