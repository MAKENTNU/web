from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag()
def get_semantic_flag_code_from_language_code(language_code):
    return {
        "nb": "no",
        "en": "us",
    }[language_code]


@register.simple_tag()
def get_local_name_from_language_code(language_code):
    return {
        "nb": _("Norwegian"),
        "en": _("English"),
    }[language_code]
