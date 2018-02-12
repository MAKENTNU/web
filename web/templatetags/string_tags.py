from django import template

register = template.Library()

@register.filter(name='first_word')
def first_word(string, arg=' '):
    return string.split(arg)[0]
