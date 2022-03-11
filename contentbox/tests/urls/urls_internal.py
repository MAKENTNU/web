from django.conf.urls.i18n import i18n_patterns
from django.urls import path

from internal.urls import urlpatterns as internal_urlpatterns
from ...views import DisplayContentBoxView, EditContentBoxView


INTERNAL_TEST_TITLE = 'internal_test_title'
internal_change_perm = 'contentbox.perm1'


class InternalDisplayContentBoxView(DisplayContentBoxView):
    extra_context = {
        'base_template': 'internal/base.html',
    }

    change_perms = (internal_change_perm,)


urlpatterns = i18n_patterns(
    InternalDisplayContentBoxView.get_path(INTERNAL_TEST_TITLE),
    path("contentbox/<int:pk>/edit/",
         EditContentBoxView.as_view(
             permission_required=EditContentBoxView.permission_required + (internal_change_perm,),
             base_template='internal/base.html',
         ), name='contentbox_edit'),

    prefix_default_language=False,
) + internal_urlpatterns  # should be appended, so that they can be overridden by the above patterns
