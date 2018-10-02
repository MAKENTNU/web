from django import template

register = template.Library()


@register.simple_tag()
def get_3d_quota(user):
    pass
    #return Quota3D.get_quota(user)


@register.simple_tag()
def get_sewing_quota(user):
    pass
    #return QuotaSewing.get_quota(user)
