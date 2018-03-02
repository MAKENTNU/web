from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.views.static import serve
from social_core.utils import setting_name

from contentbox.models import ContentBox
from dataporten.views import Logout, login_wrapper

from web.views import IndexView

extra = getattr(settings, setting_name('TRAILING_SLASH'), True) and '/' or ''

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', IndexView.as_view()),
    url(r'^login/$', RedirectView.as_view(url='/login/dataporten/'), name='login'),
    url(r'^logout/$', Logout.as_view(), name='logout'),
    url(r'^complete/(?P<backend>[^/]+){0}$'.format(extra), login_wrapper),
    url(r'', include('social_django.urls', namespace='social')),
    url(r'^news/', include('news.urls')),
    url(r'^contentbox/', include('contentbox.urls')),
    url(r'^$', IndexView.as_view()),
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}), # local only, nginx in prod
    ContentBox.url('about'),
    ContentBox.url('makerspace'),
    ContentBox.url('cookies'),
    ContentBox.url('rules'),
    url(r'^checkin/', include('checkin.urls')),
]
