from django.conf import settings
from django_hosts import host


host_patterns = [
    host(r"(i|internal|internt)", 'internal.urls', name='internal'),
    host(r"admin", 'web.admin_urls', name='admin'),
    host(r"docs", 'docs.urls', name='docs'),
    host(r"", settings.ROOT_URLCONF, name='main'),
]
