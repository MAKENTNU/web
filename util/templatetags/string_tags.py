from django import template

register = template.Library()


@register.filter
def first_word(string, arg=" "):
    return string.split(arg)[0]
