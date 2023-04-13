from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views import defaults
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from social_core.utils import setting_name

from contentbox.views import ContentBoxDetailView, ContentBoxUpdateView
from dataporten.views import login_wrapper
from news import urls as news_urls
from util.url_utils import ckeditor_uploader_urls, debug_toolbar_urls, logout_urls
from . import views


extra = "/" if getattr(settings, setting_name('TRAILING_SLASH'), True) else ""

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name='web/robots.txt', content_type='text/plain')),
    path(".well-known/security.txt", TemplateView.as_view(template_name='web/security.txt', content_type='text/plain')),

    *debug_toolbar_urls(),
    path("i18n/", include('django.conf.urls.i18n')),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),  # For development only; Nginx is used in production

    *ckeditor_uploader_urls(),
]

admin_urlpatterns = [
    path("", views.AdminPanelView.as_view(), name='admin_panel'),
    path("news/", include(news_urls.adminpatterns)),
]

content_box_urlpatterns = [
    path("<int:pk>/change/", ContentBoxUpdateView.as_view(base_template='web/base.html'), name='content_box_update'),
]

about_urlpatterns = [
    path("", views.AboutUsView.as_view(url_name='about'), name='about'),
    ContentBoxDetailView.get_path('contact'),
]

urlpatterns += i18n_patterns(
    path("", views.IndexPageView.as_view(), name='index_page'),
    path("admin/", decorator_include(login_required, admin_urlpatterns)),

    # App paths:
    path("announcements/", include('announcements.urls')),
    path("checkin/", include('checkin.urls')),
    path("committees/", include('groups.urls')),
    path("faq/", include('faq.urls')),
    path("makerspace/", include('makerspace.urls')),
    path("news/", include('news.urls')),
    path("reservation/", include('make_queue.urls')),

    # ContentBox paths:
    path("contentbox/", include(content_box_urlpatterns)),
    path("about/", include(about_urlpatterns)),
    *ContentBoxDetailView.get_multi_path('apply', 'søk', 'sok'),
    ContentBoxDetailView.get_path('cookies'),
    ContentBoxDetailView.get_path('privacypolicy'),

    # This path must be wrapped by `i18n_patterns()`
    # (see https://docs.djangoproject.com/en/stable/topics/i18n/translation/#django.views.i18n.JavaScriptCatalog)
    path("jsi18n/", JavaScriptCatalog.as_view(), name='javascript_catalog'),

    prefix_default_language=False,
)

# Configure login based on if we have configured Dataporten or not.
if settings.USES_DATAPORTEN_AUTH:
    urlpatterns += i18n_patterns(
        path("login/", RedirectView.as_view(url="/login/dataporten/", query_string=True), name='login'),

        # This line must come before including `social_django.urls` below, to override social_django's `complete` view
        re_path(rf"^complete/(?P<backend>[^/]+){extra}$", login_wrapper),
        path("", include('social_django.urls', namespace='social')),

        prefix_default_language=False,
    )
else:
    # If it is not configured, we would like to have a simple login page. So that
    # we can test with non-superusers without giving them access to the admin page.
    urlpatterns += i18n_patterns(
        path("login/", auth_views.LoginView.as_view(
            template_name='web/login.html',
            redirect_authenticated_user=True,
            # This allows the `next` query parameter (used when logging in) to redirect to pages on all the subdomains
            success_url_allowed_hosts=set(settings.ALLOWED_REDIRECT_HOSTS),
        ), name='login'),

        prefix_default_language=False,
    )
urlpatterns += logout_urls()

# --- Old URLs ---
# URLs kept for "backward-compatibility" after paths were changed, so that users are simply redirected to the new URLs.
# These need only be URLs for pages that are likely to be linked to.
urlpatterns += i18n_patterns(
    path("rules/", RedirectView.as_view(pattern_name='rules', permanent=True)),
    path("reservation/rules/<int:pk>/", RedirectView.as_view(pattern_name='reservation_rule_list', permanent=True)),
    path("reservation/rules/usage/<int:pk>/", RedirectView.as_view(pattern_name='machine_usage_rule_detail', permanent=True)),

    path("news/article/<int:pk>/", RedirectView.as_view(pattern_name='article_detail', permanent=True)),
    path("news/event/<int:pk>/", RedirectView.as_view(pattern_name='event_detail', permanent=True)),
    path("news/ticket/<uuid:pk>/", RedirectView.as_view(pattern_name='event_ticket_detail', permanent=True)),
    path("news/ticket/me/", RedirectView.as_view(pattern_name='event_ticket_my_list', permanent=True)),

    prefix_default_language=False,
)


# These handlers are automatically registered by Django
# (see https://docs.djangoproject.com/en/stable/topics/http/views/#customizing-error-views)

def handler404(request, exception):
    return defaults.page_not_found(request, exception=exception, template_name='web/404.html')


def handler500(request):
    return defaults.server_error(request, template_name='web/500.html')
