from django import template
from make_queue.models import Quota3D, QuotaSewing

register = template.Library()


@register.simple_tag()
def get_3d_quota(user):
    return Quota3D.get_quota(user)


@register.simple_tag()
def get_sewing_quota(user):
    return QuotaSewing.get_quota(user)
