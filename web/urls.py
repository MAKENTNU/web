from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.views.decorators.cache import never_cache
from django.views.i18n import JavaScriptCatalog
from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic.base import RedirectView
from django.views.static import serve
from social_core.utils import setting_name

from contentbox.models import ContentBox
from dataporten.views import Logout, login_wrapper
from web.views import IndexView, AdminPanelView, View404, View500
from ckeditor_uploader import views as ckeditor_views

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('robots.txt', TemplateView.as_view(template_name='web/robots.txt', content_type='text/plain')),
]

urlpatterns += i18n_patterns(
    path('reservation/', include('make_queue.urls')),
    path('adminpanel/', AdminPanelView.as_view(), name='adminpanel'),
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='front-page'),
    path('login/', RedirectView.as_view(url='/login/dataporten/'), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
    re_path(r'^complete/(?P<backend>[^/]+){0}$'.format(extra), login_wrapper),
    path('', include('social_django.urls', namespace='social')),
    path('news/', include('news.urls')),
    path('contentbox/', include('contentbox.urls')),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),  # local only, nginx in prod
    path('checkin/', include('checkin.urls')),
    path('committees/', include('groups.urls')),
    ContentBox.url('about'),
    ContentBox.url('makerspace'),
    ContentBox.url('cookies'),
    ContentBox.url('rules'),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    prefix_default_language=False,
)

# CKEditor URLs
urlpatterns += [
    path('ckeditor/upload/', permission_required("contentbox.can_upload_image")(ckeditor_views.upload), name='ckeditor_upload'),
    path('ckeditor/browse/', never_cache(permission_required("contentbox.can_browse_image")(ckeditor_views.browse)), name='ckeditor_browse'),
]

handler404 = View404.as_view()
handler500 = View500.as_view()
