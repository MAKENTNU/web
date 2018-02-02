from django.conf.urls import url

from news.views import EditArticleView, CreateArticleView, EditEventView, CreateEventView, ViewArticleView, \
    ViewEventView, AdminView, ViewEventsView, ViewArticlesView

urlpatterns = [
    url('^admin/$', AdminView.as_view(), name='admin'),
    url('^articles/$', ViewArticlesView.as_view(), name='articles'),
    url('^article/create/$', CreateArticleView.as_view(), name='article-create'),
    url('^article/(?P<pk>[0-9]+)/edit/$', EditArticleView.as_view(), name='article-edit'),
    url('^article/(?P<pk>[0-9]+)/$', ViewArticleView.as_view(), name='article'),
    url('^events/$', ViewEventsView.as_view(), name='events'),
    url('^event/create/$', CreateEventView.as_view(), name='event-create'),
    url('^event/(?P<pk>[0-9]+)/edit/$', EditEventView.as_view(), name='event-edit'),
    url('^event/(?P<pk>[0-9]+)/$', ViewEventView.as_view(), name='event'),
]
