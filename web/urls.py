from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from dataporten.views import Logout
from web.views import IndexView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', IndexView.as_view()),
    url(r'^login/$', RedirectView.as_view(url='/login/dataporten/')),
    url(r'^logout/$', Logout.as_view()),
    url(r'', include('social_django.urls', namespace='social')),
]
