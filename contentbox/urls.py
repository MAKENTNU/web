from django.conf.urls import url

from contentbox.views import EditContentBoxView

urlpatterns = [
    url('^(?P<pk>[0-9]+)/edit/$', EditContentBoxView.as_view()),
]
