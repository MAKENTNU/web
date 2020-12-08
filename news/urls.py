from django.contrib.auth.decorators import login_required, permission_required
from django.urls import path

from . import views
from .ical import SingleTimePlaceFeed


urlpatterns = [
    path('admin/articles/', login_required(views.AdminArticleListView.as_view()), name='admin_article_list'),
    path('admin/events/', login_required(views.AdminEventListView.as_view()), name='admin_event_list'),
    path('admin/toggle/article/', login_required(views.AdminArticleToggleView.as_view()), name='article-toggle'),
    path('admin/toggle/event/', login_required(views.AdminEventToggleView.as_view()), name='event-toggle'),
    path('admin/toggle/timeplace/', login_required(views.AdminTimeplaceToggleView.as_view()), name='timeplace-toggle'),
    path('admin/event/<int:pk>/', permission_required("news.change_event")(views.AdminEventDetailView.as_view()), name='admin_event_detail'),
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('article/create/', login_required(views.CreateArticleView.as_view()), name='article-create'),
    path('article/<int:pk>/edit/', login_required(views.EditArticleView.as_view()), name='article-edit'),
    path('article/<int:pk>/delete/', login_required(views.DeleteArticleView.as_view()), name='article-delete'),
    path('article/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('event/create/', login_required(views.CreateEventView.as_view()), name='event-create'),
    path('event/<int:pk>/edit/', login_required(views.EditEventView.as_view()), name='event-edit'),
    path('event/<int:pk>/tickets/', permission_required("news.change_event")(views.AdminEventTicketListView.as_view()), name='event_ticket_list'),
    path('event/<int:pk>/delete/', login_required(views.DeleteEventView.as_view()), name='event-delete'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('event/<int:event_pk>/register/', login_required(views.EventRegistrationView.as_view()), name="register-event"),
    path('timeplace/<int:pk>/edit/', login_required(views.EditTimePlaceView.as_view()), name='timeplace-edit'),
    path('timeplace/<int:pk>/duplicate/', login_required(views.DuplicateTimePlaceView.as_view()), name='timeplace-duplicate'),
    path('timeplace/<int:event_pk>/create/', login_required(views.CreateTimePlaceView.as_view()), name='timeplace_create'),
    path('timeplace/<int:pk>/tickets/', permission_required("news.change_event")(views.AdminTimeplaceTicketListView.as_view()),
         name='timeplace_ticket_list'),
    path('timeplace/<int:pk>/delete/', login_required(views.DeleteTimePlaceView.as_view()), name='timeplace-delete'),
    path('timeplace/<int:pk>/ical/', SingleTimePlaceFeed(), name='timeplace-ical'),
    path('timeplace/<int:timeplace_pk>/register/', login_required(views.EventRegistrationView.as_view()), name="register-timeplace"),
    path('ticket/<uuid:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('ticket/<uuid:pk>/cancel/', views.CancelTicketView.as_view(), name="cancel-ticket"),
    path('ticket/me/', login_required(views.MyTicketsListView.as_view()), name='my_tickets_list'),
]
