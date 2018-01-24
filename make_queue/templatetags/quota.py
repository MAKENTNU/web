from django import template
from make_queue.models import Quota3D, QuotaSewing

register = template.Library()


@register.simple_tag()
def get_3d_quota(user):
    if hasattr(user, "quota3d"):
        return user.quota3d
    return Quota3D.objects.create(user=user)


@register.simple_tag()
def get_sewing_quota(user):
    if hasattr(user, "quotasewing"):
        return user.quotasewing
    return QuotaSewing.objects.create(user=user)
