from django import template

register = template.Library()


@register.simple_tag()
def get_absolute_uri_no_query(request):
    """
    Returns the absolute URI of the request with no query parameters

    :param request: The request
    :return: The URI of the request page
    """
    return request.build_absolute_uri(request.path)
