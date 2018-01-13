from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.static import serve

from web.views import IndexView

urlpatterns = [
    url(r'^reservation/', include('make_queue.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^news/', include('news.urls')),
    url(r'^$', IndexView.as_view()),
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        })
    ]
