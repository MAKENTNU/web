from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag()
def set_current_date(shift_hours=0):
    return (timezone.now() + timezone.timedelta(hours=shift_hours)).strftime("%m/%d/%Y %H:%M")


@register.simple_tag()
def set_current_date_only():
    return timezone.now().strftime("%Y-%m-%d")
