from django.contrib.auth.views import SuccessURLAllowedHostsMixin
from django_hosts import host

from web import settings

host_patterns = (
    host(r"(i|internal|internt)", "internal.urls", name="internal"),
    host(r"admin", "web.admin-urls", name="admin"),
    host(r"", settings.ROOT_URLCONF, name="main"),
)

# A list of all possible subdomains
subdomains = (
    "i", "internal", "internt", "admin", ""
)

# This allows the next parameter in login to redirect to pages on all the subdomains
SuccessURLAllowedHostsMixin.success_url_allowed_hosts = {
    f"{subdomain}.{settings.PARENT_HOST}" for subdomain in subdomains
}
