from django import template

register = template.Library()


@register.filter
def first_word(string, arg=" "):
    return string.split(arg)[0]


@register.simple_tag
def invert(expression):
    return "true" if not expression else "false"
