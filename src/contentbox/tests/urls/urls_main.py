from django.conf.urls.i18n import i18n_patterns

from contentbox.views import ContentBoxDetailView
from web.urls import urlpatterns as base_urlpatterns

TEST_URL_NAME = "test_url_name"
TEST_MULTI_URL_NAMES = ("test_main", "test_alt1", "test_alt2")

urlpatterns = i18n_patterns(
    ContentBoxDetailView.get_path(TEST_URL_NAME),
    *ContentBoxDetailView.get_multi_path(*TEST_MULTI_URL_NAMES),
    prefix_default_language=False,
)
urlpatterns += base_urlpatterns
