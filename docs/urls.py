from decorator_include import decorator_include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path, register_converter
from django.views.generic import TemplateView
from django_hosts import reverse

from . import converters, views
from .models import Page


register_converter(converters.PageByTitle, "page")
register_converter(converters.ContentByPk, "content")

unsafe_urlpatterns = [
    path("", views.DocumentationPageView.as_view(), {"pk": Page.objects.get_or_create(title="Documentation")[0].pk}, name="home"),
    path("page/<page:pk>/", views.DocumentationPageView.as_view(), name="page"),
    path("page/<page:pk>/history/", views.HistoryDocumentationPageView.as_view(), name="page-history"),
    path("page/<page:pk>/history/change/", views.ChangeDocumentationPageVersionView.as_view(), name="change-page-version"),
    path("page/<page:pk>/history/<content:content>/", views.OldDocumentationPageContentView.as_view(), name="old-page-content"),
    path("page/new/create/", views.CreateDocumentationPageView.as_view(), name="create-page"),
    path("page/<page:pk>/edit/", views.EditDocumentationPageView.as_view(), name="edit-page"),
    path("page/<page:pk>/delete/", views.DeleteDocumentationPageView.as_view(), name="delete-page"),
    path("search/", views.SearchPagesView.as_view(), name="search-pages"),
]

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="docs/robots.txt", content_type="text/plain")),
    path("i18n/", decorator_include(
        permission_required("docs.view_page", login_url=reverse("login", host="main")),
        "django.conf.urls.i18n"
    )),
]

urlpatterns += i18n_patterns(
    path("", decorator_include(
        permission_required("docs.view_page", login_url=reverse("login", host="main")),
        unsafe_urlpatterns
    )),
    prefix_default_language=False
)
