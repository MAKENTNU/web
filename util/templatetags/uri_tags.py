from django import template

register = template.Library()


@register.simple_tag
def get_absolute_uri_for_path(request, path: str):
    """
    :param request: the request object
    :param path: the path to append to the request's scheme and host
    :return: The absolute URI of the provided path.
    """
    return request.build_absolute_uri(path)


@register.simple_tag
def get_absolute_uri_no_query(request):
    """
    :param request: the request object
    :return: The absolute URI of the requested page, without any query parameters.
    """
    return get_absolute_uri_for_path(request, request.path)
