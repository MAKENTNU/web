from django import template

register = template.Library()


@register.simple_tag
def img_square(size_px):
    return f"width: {size_px}px; height: {size_px}px; object-fit: cover;"
