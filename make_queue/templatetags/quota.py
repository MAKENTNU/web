from django import template

register = template.Library()


@register.simple_tag()
def get_active_reservations(quota, user):
    return quota.get_active_reservations(user)
