from ckeditor_uploader import views as ckeditor_views
from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import include, path, re_path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve
from social_core.utils import setting_name

from contentbox.views import DisplayContentBoxView, EditContentBoxView
from dataporten.views import Logout, login_wrapper
from news import urls as news_urls
from util.url_utils import debug_toolbar_urls
from . import views


extra = "/" if getattr(settings, setting_name('TRAILING_SLASH'), True) else ""

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name='web/robots.txt', content_type='text/plain')),
    path(".well-known/security.txt", TemplateView.as_view(template_name='web/security.txt', content_type='text/plain')),

    *debug_toolbar_urls(),
    path("i18n/", include('django.conf.urls.i18n')),
]

admin_urlpatterns = [
    path("", views.AdminPanelView.as_view(), name='adminpanel'),
    path("news/", include(news_urls.adminpatterns)),
]

contentbox_urlpatterns = [
    path("<int:pk>/edit/", EditContentBoxView.as_view(base_template='web/base.html'), name='contentbox_edit'),
]

about_urlpatterns = [
    path("", views.AboutUsView.as_view(url_name='about'), name='about'),
    DisplayContentBoxView.get_path('contact'),
]

urlpatterns += i18n_patterns(
    path("", views.IndexView.as_view(), name='front_page'),
    path("admin/", decorator_include(login_required, admin_urlpatterns)),
    path("reservation/", include('make_queue.urls')),
    path("news/", include('news.urls')),
    path("contentbox/", include(contentbox_urlpatterns)),
    path("media/<path:path>", serve, {'document_root': settings.MEDIA_ROOT}),  # for development only; Nginx is used in production
    path("checkin/", include('checkin.urls')),
    path("committees/", include('groups.urls')),
    path("announcements/", include('announcements.urls')),
    path("about/", include(about_urlpatterns)),
    path("makerspace/", include('makerspace.urls')),
    path("faq/", include('faq.urls')),
    *DisplayContentBoxView.get_multi_path('apply', 'søk', 'sok'),
    DisplayContentBoxView.get_path('cookies'),
    DisplayContentBoxView.get_path('privacypolicy'),

    path("jsi18n/", JavaScriptCatalog.as_view(), name='javascript_catalog'),

    prefix_default_language=False,
)

# Configure login based on if we have configured Dataporten or not.
if settings.SOCIAL_AUTH_DATAPORTEN_SECRET:
    urlpatterns += i18n_patterns(
        path("login/", RedirectView.as_view(url="/login/dataporten/", query_string=True), name='login'),
        path("logout/", Logout.as_view(), name='logout'),

        # Should come before `social_django.urls` below, to override social_django's `complete` view
        re_path(rf"^complete/(?P<backend>[^/]+){extra}$", login_wrapper),
        path("", include('social_django.urls', namespace='social')),

        prefix_default_language=False,
    )
else:
    # If it is not configured, we would like to have a simple login page. So that
    # we can test with non-superusers without giving them access to the admin page.
    urlpatterns += i18n_patterns(
        path("login/", auth_views.LoginView.as_view(template_name='web/login.html', redirect_authenticated_user=True), name='login'),
        path("logout/", auth_views.LogoutView.as_view(next_page="/"), name='logout'),

        prefix_default_language=False,
    )

# CKEditor URLs
urlpatterns += [
    # Based on the URLs in https://github.com/django-ckeditor/django-ckeditor/blob/9866ebe098794eca7a5132d6f2a4b1d1d837e735/ckeditor_uploader/urls.py
    path("ckeditor/upload/", permission_required('contentbox.can_upload_image')(ckeditor_views.upload), name='ckeditor_upload'),
    path("ckeditor/browse/", never_cache(permission_required('contentbox.can_browse_image')(ckeditor_views.browse)), name='ckeditor_browse'),
]

# --- Old URLs ---
# URLs kept for "backward-compatibility" after paths were changed, so that users are simply redirected to the new URLs
urlpatterns += i18n_patterns(
    path("rules/", RedirectView.as_view(url=reverse_lazy('rules'), permanent=True)),
    path("reservation/rules/<int:pk>/", RedirectView.as_view(pattern_name='reservation_rule_list', permanent=True)),
    path("reservation/rules/usage/<int:pk>/", RedirectView.as_view(pattern_name='machine_usage_rules_detail', permanent=True)),

    path("news/article/<int:pk>/", RedirectView.as_view(pattern_name='article_detail', permanent=True)),
    path("news/event/<int:pk>/", RedirectView.as_view(pattern_name='event_detail', permanent=True)),
    path("news/ticket/<uuid:pk>/", RedirectView.as_view(pattern_name='ticket_detail', permanent=True)),
    path("news/ticket/me/", RedirectView.as_view(pattern_name='my_tickets_list', permanent=True)),

    prefix_default_language=False,
)

handler404 = views.View404.as_view()
handler500 = views.view_500
