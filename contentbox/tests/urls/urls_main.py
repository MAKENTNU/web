from django.conf.urls.i18n import i18n_patterns

from web.urls import urlpatterns as base_urlpatterns
from ...views import DisplayContentBoxView


TEST_TITLE = 'test_title'
TEST_MULTI_TITLES = ('test_main', 'test_alt1', 'test_alt2')

urlpatterns = i18n_patterns(
    DisplayContentBoxView.get_path(TEST_TITLE),
    *DisplayContentBoxView.get_multi_path(*TEST_MULTI_TITLES),

    prefix_default_language=False,
) + base_urlpatterns
