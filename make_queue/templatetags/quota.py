from django import template

register = template.Library()


@register.simple_tag
def get_unfinished_reservations(quota, user):
    return quota.get_unfinished_reservations(user)
