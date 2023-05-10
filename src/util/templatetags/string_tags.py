from django import template
from django.template.defaultfilters import stringfilter, title
from django.utils import translation

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def first_word(string: str, arg=" "):
    return string.split(arg)[0]


@register.filter(is_safe=True)
@stringfilter
def title_en(string: str):
    """Makes the string title-cased -- only if the currently set language is English."""
    if translation.get_language() == "en":
        return title(string)
    return string
