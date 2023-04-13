from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import TemplateView

from util.url_utils import ckeditor_uploader_urls, debug_toolbar_urls, logout_urls, permission_required_else_denied
from . import views


urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name='internal/robots.txt', content_type='text/plain')),
    path(".well-known/security.txt", TemplateView.as_view(template_name='web/security.txt', content_type='text/plain')),

    *debug_toolbar_urls(),
    path("i18n/", decorator_include(
        permission_required_else_denied('internal.is_internal'),
        'django.conf.urls.i18n'
    )),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),  # For development only; Nginx is used in production

    *ckeditor_uploader_urls(),
]
urlpatterns += logout_urls()

committee_bulletin_urlpatterns = [
    views.CommitteeBulletinBoardView.get_path('dev-board'),
    views.CommitteeBulletinBoardView.get_path('event-board'),
    views.CommitteeBulletinBoardView.get_path('mentor-board'),
    views.CommitteeBulletinBoardView.get_path('pr-board'),
]

internal_content_box_urlpatterns = [
    path("<int:pk>/change/", views.InternalContentBoxUpdateView.as_view(), name='content_box_update'),
]

member_urlpatterns = [
    path("members/", views.MemberListView.as_view(), name='member_list'),
    path("members/<int:pk>/", views.MemberListView.as_view(), name='member_detail'),
    path("members/add/", views.MemberCreateView.as_view(), name='member_create'),
    path("members/<int:pk>/change/", views.MemberUpdateView.as_view(), name='member_update'),
    path("members/<int:pk>/change/status/", views.MemberStatusUpdateView.as_view(), name='member_status_update'),
    path("members/<int:pk>/change/status/quit/", views.MemberQuitView.as_view(), name='member_quit'),
    path("members/<int:pk>/change/status/retire/", views.MemberRetireView.as_view(), name='member_retire'),
    path("members/<int:member_pk>/access/<int:pk>/change/", views.SystemAccessUpdateView.as_view(), name='system_access_update'),
]

secret_urlpatterns = [
    path("secrets/", views.SecretListView.as_view(), name='secret_list'),
    path("secrets/add/", views.SecretCreateView.as_view(), name='secret_create'),
    path("secrets/<int:pk>/change/", views.SecretUpdateView.as_view(), name='secret_update'),
    path("secrets/<int:pk>/delete/", views.SecretDeleteView.as_view(), name='secret_delete'),
]

quote_urlpatterns = [
    path("quotes/", views.QuoteListView.as_view(), name='quote_list'),
    path("quotes/add/", views.QuoteCreateView.as_view(), name='quote_create'),
    path("quotes/<int:pk>/change/", views.QuoteUpdateView.as_view(), name='quote_update'),
    path("quotes/<int:pk>/delete/", views.QuoteDeleteView.as_view(), name='quote_delete'),
]

internal_urlpatterns = [
    path("", views.HomeView.as_view(url_name='home'), name='home'),
    path("bulletins/", include(committee_bulletin_urlpatterns)),
    # The proper `url_name` for this would be `MAKE-history`, but the validator of the model's field requires it to be lowercase
    views.InternalContentBoxDetailView.get_path('make-history'),
    path("contentbox/", include(internal_content_box_urlpatterns)),

    path("", decorator_include(
        permission_required_else_denied('internal.view_member'),
        member_urlpatterns
    )),
    path("", decorator_include(
        permission_required_else_denied('internal.view_secret'),
        secret_urlpatterns
    )),
    path("", decorator_include(
        permission_required_else_denied('internal.view_quote'),
        quote_urlpatterns
    )),
]

urlpatterns += i18n_patterns(
    path("", decorator_include(
        permission_required_else_denied('internal.is_internal'),
        internal_urlpatterns
    )),

    prefix_default_language=False,
)
