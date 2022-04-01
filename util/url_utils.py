from django.conf import settings
from django.urls import include, path


def debug_toolbar_urls():
    if not settings.USE_DEBUG_TOOLBAR:
        return []
    return [
        path("__debug__/", include('debug_toolbar.urls')),
    ]
