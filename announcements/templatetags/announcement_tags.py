from django import template

from ..models import Announcement

register = template.Library()


@register.simple_tag()
def announcement_css_class(announcement):
    return {
        Announcement.Type.INFO: "info",
        Announcement.Type.WARNING: "warning",
        Announcement.Type.CRITICAL: "critical",
    }[announcement.classification]


@register.simple_tag()
def site_wide_announcements():
    return Announcement.objects.valid_site_wide()


@register.simple_tag()
def non_site_wide_announcements():
    return Announcement.objects.valid_non_site_wide()
