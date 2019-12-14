from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path, include
from django.views.generic import TemplateView
from django_hosts import reverse

from web.url_util import decorated_includes

unsafe_urlpatterns = [
]

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="docs/robots.txt", content_type="text/plain")),
    path("i18n/", decorated_includes(
        permission_required("docs.can_view", login_url=reverse("login", host="main")),
        include("django.conf.urls.i18n")
    )),
]

urlpatterns += i18n_patterns(
    path("", decorated_includes(
        permission_required("internal.is_internal", login_url=reverse("login", host="main")),
        include(unsafe_urlpatterns)
    )),
    prefix_default_language=False
)
