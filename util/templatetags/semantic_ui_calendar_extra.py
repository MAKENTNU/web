from django import template
from django.utils import timezone

from util.locale_utils import iso_datetime_format

register = template.Library()


@register.simple_tag
def set_current_date(shift_hours=0):
    return iso_datetime_format(timezone.now() + timezone.timedelta(hours=shift_hours))


@register.simple_tag
def set_current_date_only():
    return str(timezone.localdate())
