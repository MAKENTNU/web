from copy import copy

from internal.urls import urlpatterns as internal_urlpatterns
from web.hosts import host_patterns as base_host_patterns


# Have to copy the patterns/paths, to not change their attributes for other tests in the same test run
# (can't deepcopy, as some attributes deeper down are apparently not copyable or cause infinite recursion)
host_patterns = [copy(p) for p in base_host_patterns]

# Set the `urlconf` of the internal host to be this file,
# which makes it use the `urlpatterns` defined below as the internal urlpatterns
_internal_host_index = None
for i, pattern in enumerate(host_patterns):
    if pattern.name == 'internal':
        _internal_host_index = i
host_patterns[_internal_host_index].urlconf = __name__

# [See comment on `host_patterns` above]
urlpatterns = [copy(p) for p in internal_urlpatterns]
