from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='first_word')
def first_word(string, arg=' '):
    return string.split(arg)[0]
