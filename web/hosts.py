import django_hosts
from ckeditor_uploader import widgets as ckeditor_uploader_widgets
from django.conf import settings
from django.contrib.auth.views import SuccessURLAllowedHostsMixin
from django_hosts import host


# Monkey patch Django's `reverse()` function, to make it work with subdomains
ckeditor_uploader_widgets.reverse = django_hosts.reverse

host_patterns = [
    host(r"(i|internal|internt)", "internal.urls", name="internal"),
    host(r"admin", "web.admin_urls", name="admin"),
    host(r"docs", "docs.urls", name="docs"),
    host(r"", settings.ROOT_URLCONF, name="main"),
]

# This allows the next parameter in login to redirect to pages on all the subdomains
SuccessURLAllowedHostsMixin.success_url_allowed_hosts = set(settings.ALLOWED_REDIRECT_HOSTS)
