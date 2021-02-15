from django import template

register = template.Library()


@register.simple_tag()
def form_has_error(form, field, error_code):
    return form.has_error(field, error_code)
