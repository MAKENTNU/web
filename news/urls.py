from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from news.views import EditArticleView, CreateArticleView, EditEventView, CreateEventView, ViewArticleView, \
    ViewEventView, AdminView, ViewEventsView, ViewArticlesView, CreateTimePlaceView, EditTimePlaceView, \
    DuplicateTimePlaceView, NewTimePlaceView, AdminArticleToggleView, AdminEventToggleView, AdminTimeplaceToggleView

urlpatterns = [
    url('^admin/$', login_required(AdminView.as_view()), name='admin'),
    url('^admin/toggle/article/$', login_required(AdminArticleToggleView.as_view()), name='article-toggle'),
    url('^admin/toggle/event/$', login_required(AdminEventToggleView.as_view()), name='event-toggle'),
    url('^admin/toggle/timeplace/$', login_required(AdminTimeplaceToggleView.as_view()), name='timeplace-toggle'),
    url('^articles/$', ViewArticlesView.as_view(), name='articles'),
    url('^article/create/$', login_required(CreateArticleView.as_view()), name='article-create'),
    url('^article/(?P<pk>[0-9]+)/edit/$', login_required(EditArticleView.as_view()), name='article-edit'),
    url('^article/(?P<pk>[0-9]+)/$', ViewArticleView.as_view(), name='article'),
    url('^events/$', ViewEventsView.as_view(), name='events'),
    url('^event/create/$', login_required(CreateEventView.as_view()), name='event-create'),
    url('^event/(?P<pk>[0-9]+)/edit/$', login_required(EditEventView.as_view()), name='event-edit'),
    url('^event/(?P<pk>[0-9]+)/$', ViewEventView.as_view(), name='event'),
    url('^timeplace/create/$', login_required(CreateTimePlaceView.as_view()), name='timeplace-create'),
    url('^timeplace/(?P<pk>[0-9]+)/edit/$', login_required(EditTimePlaceView.as_view()), name='timeplace-edit'),
    url('^timeplace/(?P<pk>[0-9]+)/duplicate/$', login_required(DuplicateTimePlaceView.as_view()),
        name='timeplace-duplicate'),
    url('^timeplace/(?P<pk>[0-9]+)/new/$', login_required(NewTimePlaceView.as_view()), name='timeplace-new'),
]
