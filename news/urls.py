from django.conf.urls import url

from news.views import EditArticleView, CreateArticleView, EditEventView, CreateEventView, AllView, ViewArticleView, ViewEventView

urlpatterns = [
    url('^all/$', AllView.as_view()),
    url('^article/create/$', CreateArticleView.as_view()),
    url('^article/(?P<pk>[0-9]+)/edit/$', EditArticleView.as_view()),
    url('^article/(?P<pk>[0-9]+)/$', ViewArticleView.as_view()),
    url('^event/create/$', CreateEventView.as_view()),
    url('^event/(?P<pk>[0-9]+)/edit/$', EditEventView.as_view()),
    url('^event/(?P<pk>[0-9]+)/$', ViewEventView.as_view()),
]
