from django.contrib.auth.decorators import login_required, permission_required
from django.urls import path

from news.ical import SingleTimePlaceFeed
from news.views import EditArticleView, CreateArticleView, EditEventView, CreateEventView, ViewArticleView, \
    ViewEventView, AdminView, ViewEventsView, ViewArticlesView, EditTimePlaceView, \
    DuplicateTimePlaceView, NewTimePlaceView, AdminArticleToggleView, AdminEventToggleView, AdminTimeplaceToggleView, \
    DeleteArticleView, DeleteTimePlaceView, DeleteEventView, AdminEventView, EventRegistrationView, TicketView, \
    ClaimTicketView

urlpatterns = [
    path('admin/', login_required(AdminView.as_view()), name='admin'),
    path('admin/toggle/article/', login_required(AdminArticleToggleView.as_view()), name='article-toggle'),
    path('admin/toggle/event/', login_required(AdminEventToggleView.as_view()), name='event-toggle'),
    path('admin/toggle/timeplace/', login_required(AdminTimeplaceToggleView.as_view()), name='timeplace-toggle'),
    path('admin/event/<int:pk>/', permission_required("news.change_event")(AdminEventView.as_view()), name='admin-event'),
    path('articles/', ViewArticlesView.as_view(), name='articles'),
    path('article/create/', login_required(CreateArticleView.as_view()), name='article-create'),
    path('article/<int:pk>/edit/', login_required(EditArticleView.as_view()), name='article-edit'),
    path('article/<int:pk>/delete/', login_required(DeleteArticleView.as_view()), name='article-delete'),
    path('article/<int:pk>/', ViewArticleView.as_view(), name='article'),
    path('events/', ViewEventsView.as_view(), name='events'),
    path('event/create/', login_required(CreateEventView.as_view()), name='event-create'),
    path('event/<int:pk>/edit/', login_required(EditEventView.as_view()), name='event-edit'),
    path('event/<int:pk>/delete/', login_required(DeleteEventView.as_view()), name='event-delete'),
    path('event/<int:pk>/', ViewEventView.as_view(), name='event'),
    path('event/<int:event_pk>/register/', EventRegistrationView.as_view(), name="register-event"),
    path('timeplace/<int:pk>/edit/', login_required(EditTimePlaceView.as_view()), name='timeplace-edit'),
    path('timeplace/<int:pk>/duplicate/', login_required(DuplicateTimePlaceView.as_view()),
         name='timeplace-duplicate'),
    path('timeplace/<int:pk>/new/', login_required(NewTimePlaceView.as_view()), name='timeplace-new'),
    path('timeplace/<int:pk>/delete/', login_required(DeleteTimePlaceView.as_view()), name='timeplace-delete'),
    path('timeplace/<int:pk>/ical/', SingleTimePlaceFeed(), name='timeplace-ical'),
    path('timeplace/<int:timeplace_pk>/register/', EventRegistrationView.as_view(), name="register-timeplace"),
    path('ticket/<uuid:pk>/', TicketView.as_view(), name="ticket"),
    path('ticket/<uuid:pk>/claim/', login_required(ClaimTicketView.as_view()), name="claim-ticket"),
]
