from django import template
from django.contrib.auth.models import Permission

register = template.Library()

@register.filter(name='has_any_permissions')
def has_any_permissions(user):
    return Permission.objects.filter(user=user).exists()

