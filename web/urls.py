from ckeditor_uploader import views as ckeditor_views
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import permission_required
from django.urls import include, path, re_path, reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve
from social_core.utils import setting_name

from contentbox.views import DisplayContentBoxView
from dataporten.views import Logout, login_wrapper
from . import views


extra = "/" if getattr(settings, setting_name('TRAILING_SLASH'), True) else ""

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('robots.txt', TemplateView.as_view(template_name='web/robots.txt', content_type='text/plain')),
]

about_urlpatterns = [
    path('', views.AboutUsView.as_view(), name='about'),
    DisplayContentBoxView.get_path('contact'),
]

urlpatterns += i18n_patterns(
    path('', views.IndexView.as_view(), name='front-page'),
    path('admin/', views.AdminPanelView.as_view(), name='adminpanel'),
    path('reservation/', include('make_queue.urls')),
    path('news/', include('news.urls')),
    path('contentbox/', include('contentbox.urls')),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),  # local only, nginx in prod
    path('checkin/', include('checkin.urls')),
    path('committees/', include('groups.urls')),
    path('announcements/', include('announcements.urls')),
    path('about/', include(about_urlpatterns)),
    path('makerspace/', include('makerspace.urls')),
    path('faq/', include('faq.urls')),
    *DisplayContentBoxView.get_multi_path('apply', 'søk', 'sok'),
    DisplayContentBoxView.get_path('cookies'),
    DisplayContentBoxView.get_path('privacypolicy'),

    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    prefix_default_language=False,
)

# Configure login based on if we have configured Dataporten or not.
if settings.SOCIAL_AUTH_DATAPORTEN_SECRET:
    urlpatterns += i18n_patterns(
        path('login/', RedirectView.as_view(url='/login/dataporten/', query_string=True), name='login'),
        path('logout/', Logout.as_view(), name='logout'),

        path('', include('social_django.urls', namespace='social')),
        re_path(rf'^complete/(?P<backend>[^/]+){extra}$', login_wrapper),
        prefix_default_language=False,
    )
else:
    # If it is not configured, we would like to have a simple login page. So that
    # we can test with non-superusers without giving them access to the admin page.
    urlpatterns += i18n_patterns(
        path('login/', auth_views.LoginView.as_view(template_name='web/login.html', redirect_authenticated_user=True), name='login'),
        path('logout/', auth_views.LogoutView.as_view(next_page="/"), name='logout'),
        prefix_default_language=False,
    )

# CKEditor URLs
urlpatterns += [
    path('ckeditor/upload/', permission_required("contentbox.can_upload_image")(ckeditor_views.upload), name='ckeditor_upload'),
    path('ckeditor/browse/', never_cache(permission_required("contentbox.can_browse_image")(ckeditor_views.browse)), name='ckeditor_browse'),
]

# --- Old URLs ---
# URLs kept for "backward-compatibility" after paths were changed, so that users are simply redirected to the new URLs
urlpatterns += i18n_patterns(
    path("rules/", RedirectView.as_view(url=reverse_lazy('rules'), permanent=True)),
    path("reservation/rules/<MachineType:machine_type>/", RedirectView.as_view(pattern_name='machine_rules', permanent=True)),
    path("reservation/rules/usage/<MachineType:machine_type>/", RedirectView.as_view(pattern_name='machine_usage_rules', permanent=True)),
    prefix_default_language=False,
)

handler404 = views.View404.as_view()
handler500 = views.view_500
