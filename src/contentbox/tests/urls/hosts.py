from django.conf import settings
from django_hosts import host

from web.settings import generate_all_hosts

# (Changing settings should be done before importing other parts of our code, as it might use these settings
# - like the login path in `web.urls`)
# Set the subdomain and host settings again, as more subdomains are added to `host_patterns` below.
settings.ALL_SUBDOMAINS = (
    *settings.ALL_SUBDOMAINS,
    'test-internal', 'test-main',
)
settings.ALLOWED_REDIRECT_HOSTS = generate_all_hosts(settings.ALL_SUBDOMAINS)

from web.hosts import host_patterns as base_host_patterns
from . import urls_internal, urls_main


host_patterns = base_host_patterns + [
    host(r"test-internal", urls_internal.__name__, name='test_internal'),
    host(r"test-main", urls_main.__name__, name='test_main'),
]

# Makes sure that the subdomain of all requests is `test-internal`
TEST_INTERNAL_CLIENT_DEFAULTS = {'SERVER_NAME': f'test-internal.{settings.PARENT_HOST}'}
