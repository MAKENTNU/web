from django.conf.urls.i18n import i18n_patterns
from django.urls import path

from internal.urls import urlpatterns as internal_urlpatterns
from ...views import ContentBoxDetailView, ContentBoxUpdateView


INTERNAL_TEST_URL_NAME = "internal_test_url_name"
internal_change_perm = "contentbox.perm1"


class InternalContentBoxDetailView(ContentBoxDetailView):
    extra_context = {
        "base_template": "internal/base.html",
    }

    change_perms = (internal_change_perm,)


urlpatterns = i18n_patterns(
    InternalContentBoxDetailView.get_path(INTERNAL_TEST_URL_NAME),
    path(
        "contentbox/<int:pk>/change/",
        ContentBoxUpdateView.as_view(
            permission_required=(
                *ContentBoxUpdateView.permission_required,
                internal_change_perm,
            ),
            base_template="internal/base.html",
        ),
        name="content_box_update",
    ),
    prefix_default_language=False,
)
# Should be appended, so that they can be overridden by the above patterns
urlpatterns += internal_urlpatterns
