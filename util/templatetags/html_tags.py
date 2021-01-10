from django import template
from django.template.defaultfilters import stringfilter, urlize
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True, needs_autoescape=True)
@stringfilter
def urlize_target_blank(value, autoescape=True):
    url: str = urlize(value, autoescape=autoescape)
    prefix, tag_start, rest = url.partition("<a ")
    # If tag start was not found:
    if not tag_start:
        return url
    return mark_safe(f'{prefix}{tag_start}target="_blank" {rest}')
