from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path, register_converter
from django.views.generic import TemplateView

from util.url_utils import ckeditor_uploader_urls, debug_toolbar_urls, logout_urls, permission_required_else_denied
from . import converters, views


register_converter(converters.SpecificPageByTitle, 'PageTitle')

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name='docs/robots.txt', content_type='text/plain')),
    path(".well-known/security.txt", TemplateView.as_view(template_name='web/security.txt', content_type='text/plain')),

    *debug_toolbar_urls(),
    path("i18n/", decorator_include(permission_required_else_denied('docs.view_page'), 'django.conf.urls.i18n')),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),  # For development only; Nginx is used in production

    *ckeditor_uploader_urls(),
]
urlpatterns += logout_urls()

specific_documentation_page_urlpatterns = [
    path("", views.DocumentationPageDetailView.as_view(), name='documentation_page_detail'),
    path("history/", views.DocumentationPageHistoryDetailView.as_view(), name='documentation_page_history_detail'),
    path("history/change/", views.DocumentationPageVersionUpdateView.as_view(), name='documentation_page_version_update'),
    path("history/<int:content_pk>/", views.DocumentationPageContentDetailView.as_view(), name='documentation_page_content_detail'),
    path("change/", views.DocumentationPageUpdateView.as_view(), name='documentation_page_update'),
    path("delete/", views.DocumentationPageDeleteView.as_view(), name='documentation_page_delete'),
]
documentation_page_urlpatterns = [
    path("add/", views.DocumentationPageCreateView.as_view(), name='documentation_page_create'),
    path("<PageTitle:title>/", include(specific_documentation_page_urlpatterns)),
]

unsafe_urlpatterns = [
    path("", views.DocumentationPageDetailView.as_view(is_main_page=True), name='home'),
    path("page/", include(documentation_page_urlpatterns)),
    path("search/", views.DocumentationPageSearchView.as_view(), name='documentation_page_search'),
]

urlpatterns += i18n_patterns(
    path("", decorator_include(permission_required_else_denied('docs.view_page'), unsafe_urlpatterns)),

    prefix_default_language=False,
)
