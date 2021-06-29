from django.conf import settings
from django.urls import include, path
from django_hosts import reverse


def reverse_internal(viewname: str, *args):
    return reverse(viewname, args=args, host='internal', host_args=['i'])


def debug_toolbar_urls():
    if not settings.USE_DEBUG_TOOLBAR:
        return []
    return [
        path("__debug__/", include('debug_toolbar.urls')),
    ]
