from django_hosts import host

from web import settings

host_patterns = (
    host(r"(i|internal|internt)", "internal.urls", name="internal"),
    host(r"admin", "web.admin-urls", name="admin"),
    host(r"", settings.ROOT_URLCONF, name="main"),
)
