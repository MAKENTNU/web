from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path, include, register_converter
from django.views.generic import TemplateView
from django_hosts import reverse

from docs import converters
from docs.models import Page
from docs.views import DocumentationPageView, EditDocumentationPageView
from web.url_util import decorated_includes

register_converter(converters.PageByTitle, "page")

unsafe_urlpatterns = [
    path("page/<page:pk>/", DocumentationPageView.as_view(), name="page"),
    path("page/<page:pk>/edit/", EditDocumentationPageView.as_view(), name="edit-page"),
    path("", DocumentationPageView.as_view(), {"pk": Page.objects.get_or_create(title="Home")[0].pk}, name="home"),
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
        permission_required("docs.can_view", login_url=reverse("login", host="main")),
        include(unsafe_urlpatterns)
    )),
    prefix_default_language=False
)
