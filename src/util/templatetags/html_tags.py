from django import template
from django.template.defaultfilters import stringfilter, urlize
from django.utils.html import format_html
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


@register.simple_tag
def anchor_tag(href, text, target_blank=True):
    extra_attrs = ""
    if target_blank:
        extra_attrs = f'{extra_attrs} target="_blank"'
    return format_html('<a href="{}"{}>{}</a>', href, mark_safe(extra_attrs), text)
