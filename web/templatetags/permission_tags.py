from django import template
from django.contrib.auth.models import Permission

register = template.Library()


@register.filter(name='has_any_permissions')
def has_any_permissions(user):
    for group in user.groups.all():
        if Permission.objects.filter(group=group).exists():
            return True
    return Permission.objects.filter(user=user).exists()


@register.filter(name='has_any_news_permissions')
def has_any_news_permissions(user):
    models = "article", "event", "timeplace"
    actions = "add", "edit", "delete"
    for m in models:
        for a in actions:
            if Permission.objects.filter(user=user, codename=a + "_" + m).exists():
                return True
    return False
