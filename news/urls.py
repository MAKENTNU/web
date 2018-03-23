from django.urls import path
from django.contrib.auth.decorators import login_required

from news.views import EditArticleView, CreateArticleView, EditEventView, CreateEventView, ViewArticleView, \
    ViewEventView, AdminView, ViewEventsView, ViewArticlesView, CreateTimePlaceView, EditTimePlaceView, \
    DuplicateTimePlaceView, NewTimePlaceView, AdminArticleToggleView, AdminEventToggleView, AdminTimeplaceToggleView

urlpatterns = [
    path('admin/', login_required(AdminView.as_view()), name='admin'),
    path('admin/toggle/article/', login_required(AdminArticleToggleView.as_view()), name='article-toggle'),
    path('admin/toggle/event/', login_required(AdminEventToggleView.as_view()), name='event-toggle'),
    path('admin/toggle/timeplace/', login_required(AdminTimeplaceToggleView.as_view()), name='timeplace-toggle'),
    path('articles/', ViewArticlesView.as_view(), name='articles'),
    path('article/create/', login_required(CreateArticleView.as_view()), name='article-create'),
    path('article/<int:pk>/edit/', login_required(EditArticleView.as_view()), name='article-edit'),
    path('article/<int:pk>/', ViewArticleView.as_view(), name='article'),
    path('events/', ViewEventsView.as_view(), name='events'),
    path('event/create/', login_required(CreateEventView.as_view()), name='event-create'),
    path('event/<int:pk>/edit/', login_required(EditEventView.as_view()), name='event-edit'),
    path('event/<int:pk>/', ViewEventView.as_view(), name='event'),
    path('timeplace/create/', login_required(CreateTimePlaceView.as_view()), name='timeplace-create'),
    path('timeplace/<int:pk>/edit/', login_required(EditTimePlaceView.as_view()), name='timeplace-edit'),
    path('timeplace/<int:pk>/duplicate/', login_required(DuplicateTimePlaceView.as_view()),
         name='timeplace-duplicate'),
    path('timeplace/<int:pk>/new/', login_required(NewTimePlaceView.as_view()), name='timeplace-new'),
]
