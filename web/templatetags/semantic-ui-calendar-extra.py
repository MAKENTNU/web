from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag()
def set_current_date():
    return timezone.now().strftime("%m/%d/%Y %H:%M")
