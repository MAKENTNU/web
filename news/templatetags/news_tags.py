from django import template
from django.db.models import Q
from django.utils import timezone

register = template.Library()


@register.filter(name='color')
def color(val):
    return 'yellow' if val else 'grey'


@register.filter(name="past")
def past(timeplace_set):
    return timeplace_set.filter(Q(end_date=timezone.now().date(), end_time__lt=timezone.now().time()) |
                                Q(end_date__lt=timezone.now().date()) |
                                Q(end_date=None, end_time__lt=timezone.now().time(), start_date=timezone.now().date()) |
                                Q(end_date=None, start_date__lt=timezone.now().date()))


@register.filter(name="future")
def future(timeplace_set):
    return timeplace_set.filter(Q(end_date=timezone.now().date(), end_time__gt=timezone.now().time()) |
                                Q(end_date__gt=timezone.now().date()) |
                                Q(end_date=None, end_time__gt=timezone.now().time(), start_date=timezone.now().date()) |
                                Q(end_date=None, start_date__gt=timezone.now().date()))
