from django_hosts import host

from web import settings

host_patterns = (
    host(r"admin", "web.admin-urls", name="admin"),
    host(r"", settings.ROOT_URLCONF, name="main"),
)
