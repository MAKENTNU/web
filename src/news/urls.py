from django.contrib.auth.decorators import login_required
from django.urls import include, path

from . import views
from .ical import SingleTimePlaceFeed


article_urlpatterns = [
    path("", views.ArticleListView.as_view(), name='article_list'),
    path("<int:pk>/", views.ArticleDetailView.as_view(), name='article_detail'),
]

specific_time_place_urlpatterns = [
    path("register/", login_required(views.EventTicketCreateView.as_view()), name='event_ticket_create'),
    path("ical/", SingleTimePlaceFeed(), name='time_place_ical'),
]

time_place_urlpatterns = [
    path("<int:time_place_pk>/", include(specific_time_place_urlpatterns)),
]

specific_event_urlpatterns = [
    path("", views.EventDetailView.as_view(), name='event_detail'),
    path("register/", login_required(views.EventTicketCreateView.as_view()), name='event_ticket_create'),
    path("timeplaces/", include(time_place_urlpatterns)),
]

event_urlpatterns = [
    path("", views.EventListView.as_view(), name='event_list'),
    path("<int:pk>/", include(specific_event_urlpatterns)),
]

ticket_urlpatterns = [
    path("<uuid:pk>/", login_required(views.EventTicketDetailView.as_view()), name='event_ticket_detail'),
    path("<uuid:pk>/cancel/", login_required(views.EventTicketCancelView.as_view()), name='event_ticket_cancel'),
    path("me/", login_required(views.EventTicketMyListView.as_view()), name='event_ticket_my_list'),
]

urlpatterns = [
    path("articles/", include(article_urlpatterns)),
    path("events/", include(event_urlpatterns)),
    path("tickets/", include(ticket_urlpatterns)),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_article_adminpatterns = [
    path("edit/", views.ArticleUpdateView.as_view(), name='article_update'),
    path("delete/", views.ArticleDeleteView.as_view(), name='article_delete'),
    path("toggle/", views.AdminAPIArticleToggleView.as_view(), name='admin_api_article_toggle'),
]

article_adminpatterns = [
    path("", views.AdminArticleListView.as_view(), name='admin_article_list'),
    path("create/", views.ArticleCreateView.as_view(), name='article_create'),
    path("<int:pk>/", include(specific_article_adminpatterns)),
]

specific_time_place_adminpatterns = [
    path("edit/", views.TimePlaceUpdateView.as_view(), name='time_place_update'),
    path("duplicate/", views.TimePlaceDuplicateCreateView.as_view(), name='time_place_duplicate_create'),
    path("delete/", views.TimePlaceDeleteView.as_view(), name='time_place_delete'),
    path("toggle/", views.AdminAPITimePlaceToggleView.as_view(), name='admin_api_time_place_toggle'),
    path("tickets/", views.AdminTimePlaceTicketListView.as_view(), name='admin_time_place_ticket_list'),
]

time_place_adminpatterns = [
    path("create/", views.TimePlaceCreateView.as_view(), name='time_place_create'),
    path("<int:time_place_pk>/", include(specific_time_place_adminpatterns)),
]

specific_event_adminpatterns = [
    path("", views.AdminEventDetailView.as_view(), name='admin_event_detail'),
    path("edit/", views.EventUpdateView.as_view(), name='event_update'),
    path("delete/", views.EventDeleteView.as_view(), name='event_delete'),
    path("toggle/", views.AdminAPIEventToggleView.as_view(), name='admin_api_event_toggle'),
    path("tickets/", views.AdminEventTicketListView.as_view(), name='admin_event_ticket_list'),
    path("timeplaces/", include(time_place_adminpatterns)),
]

event_adminpatterns = [
    path("", views.AdminEventListView.as_view(), name='admin_event_list'),
    path("create/", views.EventCreateView.as_view(), name='event_create'),
    path("<int:pk>/", include(specific_event_adminpatterns)),
    path("participants/search/", views.AdminEventParticipantsSearchView.as_view(), name='admin_event_participants_search'),
]

adminpatterns = [
    path("articles/", include(article_adminpatterns)),
    path("events/", include(event_adminpatterns)),
]
