from django.conf import settings
from django.contrib.auth.views import SuccessURLAllowedHostsMixin
from django_hosts import host

from web.hosts import host_patterns as base_host_patterns
from web.settings import generate_all_hosts
from . import urls_internal, urls_main


host_patterns = base_host_patterns + [
    host(r"test-internal", urls_internal.__name__, name='test_internal'),
    host(r"test-main", urls_main.__name__, name='test_main'),
]

# Set the subdomain and host settings again, as we have added more subdomains to `host_patterns`
settings.ALL_SUBDOMAINS = (
    *settings.ALL_SUBDOMAINS,
    'test-internal', 'test-main',
)
settings.ALLOWED_REDIRECT_HOSTS = generate_all_hosts(settings.ALL_SUBDOMAINS)
# [See the comment in `web/hosts.py`]
SuccessURLAllowedHostsMixin.success_url_allowed_hosts = set(settings.ALLOWED_REDIRECT_HOSTS)

# Makes sure that the subdomain of all requests is `test-internal`
TEST_INTERNAL_CLIENT_DEFAULTS = {'SERVER_NAME': f'test-internal.{settings.PARENT_HOST}'}
