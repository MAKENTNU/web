from django.conf.urls import url

from news.views import EditArticleView, CreateArticleView, EditEventView, CreateEventView, ViewArticleView, \
    ViewEventView, AdminView, ViewEventsView, ViewArticlesView, CreateTimePlaceView, EditTimePlaceView, \
    DuplicateTimePlaceView, NewTimePlaceView, AdminArticleToggleView, AdminEventToggleView, AdminTimeplaceToggleView

urlpatterns = [
    url('^admin/$', AdminView.as_view(), name='admin'),
    url('^admin/toggle/article/$', AdminArticleToggleView.as_view(), name='article-toggle'),
    url('^admin/toggle/event/$', AdminEventToggleView.as_view(), name='event-toggle'),
    url('^admin/toggle/timeplace/$', AdminTimeplaceToggleView.as_view(), name='timeplace-toggle'),
    url('^articles/$', ViewArticlesView.as_view(), name='articles'),
    url('^article/create/$', CreateArticleView.as_view(), name='article-create'),
    url('^article/(?P<pk>[0-9]+)/edit/$', EditArticleView.as_view(), name='article-edit'),
    url('^article/(?P<pk>[0-9]+)/$', ViewArticleView.as_view(), name='article'),
    url('^events/$', ViewEventsView.as_view(), name='events'),
    url('^event/create/$', CreateEventView.as_view(), name='event-create'),
    url('^event/(?P<pk>[0-9]+)/edit/$', EditEventView.as_view(), name='event-edit'),
    url('^event/(?P<pk>[0-9]+)/$', ViewEventView.as_view(), name='event'),
    url('^timeplace/create/$', CreateTimePlaceView.as_view(), name='timeplace-create'),
    url('^timeplace/(?P<pk>[0-9]+)/edit/$', EditTimePlaceView.as_view(), name='timeplace-edit'),
    url('^timeplace/(?P<pk>[0-9]+)/duplicate/$', DuplicateTimePlaceView.as_view(), name='timeplace-duplicate'),
    url('^timeplace/(?P<pk>[0-9]+)/new/$', NewTimePlaceView.as_view(), name='timeplace-new'),
]
