from django.conf import settings
from django_hosts import host

from web.hosts import host_patterns as base_host_patterns
from . import urls_internal, urls_main


host_patterns = base_host_patterns + [
    host(r"test-internal", urls_internal.__name__, name='test_internal'),
    host(r"test-main", urls_main.__name__, name='test_main'),
]

# Makes sure that the subdomain of all requests is `test-internal`
TEST_INTERNAL_CLIENT_DEFAULTS = {'SERVER_NAME': f'test-internal.{settings.PARENT_HOST}'}
