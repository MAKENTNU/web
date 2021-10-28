from django import template
from django.contrib.auth.models import Permission
from django.db.models import Q

from users.models import User

register = template.Library()


@register.filter
def has_any_permissions(user: User):
    return (
            Permission.objects.filter(Q(group__user=user) | Q(user=user)).exists()
            or user.is_superuser
    )


@register.filter
def has_any_article_permissions(user: User):
    return any(user.has_perm(f"news.{action}_article") for action in ["add", "change", "delete"])


@register.filter
def has_any_event_permissions(user: User):
    models = "event", "timeplace"
    actions = "add", "change", "delete"
    for model in models:
        for action in actions:
            if user.has_perm(f"news.{action}_{model}"):
                return True
    return False


@register.filter
def has_any_makerspace_permissions(user: User):
    return any(user.has_perm(f"makerspace.{action}_makerspace") for action in ["add", "change", "delete"])


@register.filter
def has_any_equipment_permissions(user: User):
    return any(user.has_perm(f"makerspace.{action}_equipment") for action in ["add", "change", "delete"])


@register.filter
def has_any_faq_permissions(user):
    return any(user.has_perm(f"faq.{action}_question") for action in ["add", "change", "delete"])
