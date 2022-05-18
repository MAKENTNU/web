from django.contrib.auth.decorators import login_required
from django.urls import include, path

from . import views
from .ical import SingleTimePlaceFeed


article_urlpatterns = [
    path("", views.ArticleListView.as_view(), name='article_list'),
    path("<int:pk>/", views.ArticleDetailView.as_view(), name='article_detail'),
]

specific_time_place_urlpatterns = [
    path("register/", login_required(views.EventRegistrationView.as_view()), name='register_timeplace'),
    path("ical/", SingleTimePlaceFeed(), name='timeplace_ical'),
]

time_place_urlpatterns = [
    path("<int:time_place_pk>/", include(specific_time_place_urlpatterns)),
]

specific_event_urlpatterns = [
    path("", views.EventDetailView.as_view(), name='event_detail'),
    path("register/", login_required(views.EventRegistrationView.as_view()), name='register_event'),
    path("timeplaces/", include(time_place_urlpatterns)),
]

event_urlpatterns = [
    path("", views.EventListView.as_view(), name='event_list'),
    path("<int:pk>/", include(specific_event_urlpatterns)),
]

ticket_urlpatterns = [
    path("<uuid:pk>/", login_required(views.TicketDetailView.as_view()), name='ticket_detail'),
    path("<uuid:pk>/cancel/", login_required(views.CancelTicketView.as_view()), name='cancel_ticket'),
    path("me/", login_required(views.MyTicketsListView.as_view()), name='my_tickets_list'),
]

urlpatterns = [
    path("articles/", include(article_urlpatterns)),
    path("events/", include(event_urlpatterns)),
    path("tickets/", include(ticket_urlpatterns)),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_article_adminpatterns = [
    path("edit/", views.EditArticleView.as_view(), name='article_edit'),
    path("delete/", views.DeleteArticleView.as_view(), name='article_delete'),
    path("toggle/", views.AdminArticleToggleView.as_view(), name='article_toggle'),
]

article_adminpatterns = [
    path("", views.AdminArticleListView.as_view(), name='admin_article_list'),
    path("create/", views.CreateArticleView.as_view(), name='article_create'),
    path("<int:pk>/", include(specific_article_adminpatterns)),
]

specific_time_place_adminpatterns = [
    path("edit/", views.EditTimePlaceView.as_view(), name='timeplace_edit'),
    path("duplicate/", views.DuplicateTimePlaceView.as_view(), name='timeplace_duplicate'),
    path("delete/", views.DeleteTimePlaceView.as_view(), name='timeplace_delete'),
    path("toggle/", views.AdminTimeplaceToggleView.as_view(), name='timeplace_toggle'),
    path("tickets/", views.AdminTimeplaceTicketListView.as_view(), name='timeplace_ticket_list'),
]

time_place_adminpatterns = [
    path("create/", views.CreateTimePlaceView.as_view(), name='timeplace_create'),
    path("<int:time_place_pk>/", include(specific_time_place_adminpatterns)),
]

specific_event_adminpatterns = [
    path("", views.AdminEventDetailView.as_view(), name='admin_event_detail'),
    path("edit/", views.EditEventView.as_view(), name='event_edit'),
    path("delete/", views.DeleteEventView.as_view(), name='event_delete'),
    path("toggle/", views.AdminEventToggleView.as_view(), name='event_toggle'),
    path("tickets/", views.AdminEventTicketListView.as_view(), name='event_ticket_list'),
    path("timeplaces/", include(time_place_adminpatterns)),
]

event_adminpatterns = [
    path("", views.AdminEventListView.as_view(), name='admin_event_list'),
    path("create/", views.CreateEventView.as_view(), name='event_create'),
    path("<int:pk>/", include(specific_event_adminpatterns)),
    path('search/', login_required(views.AdminEventsSearchView.as_view()), name='admin_events_search'),
]

adminpatterns = [
    path("articles/", include(article_adminpatterns)),
    path("events/", include(event_adminpatterns)),
]
