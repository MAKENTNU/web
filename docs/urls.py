from decorator_include import decorator_include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path, register_converter
from django.views.generic import TemplateView

from . import converters, views
from .models import MAIN_PAGE_TITLE, Page


register_converter(converters.SpecificPageByTitle, 'Page')
register_converter(converters.SpecificContent, 'Content')

unsafe_urlpatterns = [
    path("", views.DocumentationPageDetailView.as_view(), {'pk': Page.objects.get_or_create(title=MAIN_PAGE_TITLE)[0].pk}, name='home'),
    path("page/<Page:pk>/", views.DocumentationPageDetailView.as_view(), name='page_detail'),
    path("page/<Page:pk>/history/", views.HistoryDocumentationPageView.as_view(), name='page_history'),
    path("page/<Page:pk>/history/change/", views.ChangeDocumentationPageVersionView.as_view(), name='change_page_version'),
    path("page/<Page:pk>/history/<Content:content>/", views.OldDocumentationPageContentView.as_view(), name='old_page_content'),
    path("page/create/", views.CreateDocumentationPageView.as_view(), name='create_page'),
    path("page/<Page:pk>/edit/", views.EditDocumentationPageView.as_view(), name='edit_page'),
    path("page/<Page:pk>/delete/", views.DeleteDocumentationPageView.as_view(), name='delete_page'),
    path("search/", views.SearchPagesView.as_view(), name='search_pages'),
]

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name='docs/robots.txt', content_type='text/plain')),
    path(".well-known/security.txt", TemplateView.as_view(template_name='web/security.txt', content_type='text/plain')),
    path("i18n/", decorator_include(
        permission_required('docs.view_page'),
        'django.conf.urls.i18n'
    )),
]

urlpatterns += i18n_patterns(
    path("", decorator_include(
        permission_required('docs.view_page'),
        unsafe_urlpatterns
    )),

    prefix_default_language=False,
)
