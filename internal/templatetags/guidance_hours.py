from django import template
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime

register = template.Library()

@register.simple_tag()
def get_title():
    today = date.today()
    threshold = 'Jul 31'
    spring = datetime.strptime(threshold, '%b %d').date().replace(year=today.year)
    semester = _('Autumn') if today > spring else _('Spring')

    return f'{semester} {today.year}'

@register.filter
def has_reset_guidance_hours_permission(user):
    return user.has_perm("internal.change_guidancehours")
