from django import template

register = template.Library()

@register.filter(name='color')
def color(val):
    return 'yellow' if val else 'grey'
