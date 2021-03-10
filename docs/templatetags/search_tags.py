import re

from django import template

register = template.Library()


@register.simple_tag
def search_content_display(content):
    pattern = re.compile(r"<[^>]*>([^<]*)<[^>]*>", re.DOTALL)
    text = "".join(pattern.findall(content.content))
    return text[:300] + "..." * (len(text) > 300)
