from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.views.static import serve

from contentbox.models import ContentBox
from dataporten.views import Logout

from web.views import IndexView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', IndexView.as_view()),
    url(r'^login/$', RedirectView.as_view(url='/login/dataporten/')),
    url(r'^logout/$', Logout.as_view()),
    url(r'', include('social_django.urls', namespace='social')),
    url(r'^news/', include('news.urls')),
    url(r'^contentbox/', include('contentbox.urls')),
    url(r'^$', IndexView.as_view()),
    ContentBox.url('about'),
    ContentBox.url('makerspace'),
    ContentBox.url('cookies'),
    ContentBox.url('rules'),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        })
    ]
