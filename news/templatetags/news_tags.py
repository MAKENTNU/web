from django import template
from django.utils import timezone

register = template.Library()


@register.filter(name='color')
def color(val):
    return 'yellow' if val else 'grey'


@register.filter(name="past")
def past(timeplace_set):
    return timeplace_set.filter(end_time__lte=timezone.now()).order_by("-end_time")


@register.filter(name="future")
def future(timeplace_set):
    return timeplace_set.filter(end_time__gt=timezone.now())
