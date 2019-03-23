import django_hosts
from ckeditor_uploader import widgets as ckeditor_uploader_widgets
from django_hosts import host

from web import settings

# Overwrite Django's `reverse()` function, to make it work with subdomains
ckeditor_uploader_widgets.reverse = django_hosts.reverse

host_patterns = (
    host(r"(i|internal|internt)", "internal.urls", name="internal"),
    host(r"admin", "web.admin-urls", name="admin"),
    host(r"", settings.ROOT_URLCONF, name="main"),
)
