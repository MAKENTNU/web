from django.contrib.auth.decorators import login_required
from django.urls import include, path

from .api import views as api_views
from .ical import SingleTimePlaceFeed
from .views import article as article_views, event as event_views


article_urlpatterns = [
    path("", article_views.ArticleListView.as_view(), name='article_list'),
    path("<int:pk>/", article_views.ArticleDetailView.as_view(), name='article_detail'),
]

specific_time_place_urlpatterns = [
    path("register/", login_required(event_views.EventTicketCreateView.as_view()), name='event_ticket_create'),
    path("ical/", SingleTimePlaceFeed(), name='time_place_ical'),
]
time_place_urlpatterns = [
    path("<int:time_place_pk>/", include(specific_time_place_urlpatterns)),
]
specific_event_urlpatterns = [
    path("", event_views.EventDetailView.as_view(), name='event_detail'),
    path("register/", login_required(event_views.EventTicketCreateView.as_view()), name='event_ticket_create'),
    path("timeplaces/", include(time_place_urlpatterns)),
]
event_urlpatterns = [
    path("", event_views.EventListView.as_view(), name='event_list'),
    path("<int:pk>/", include(specific_event_urlpatterns)),
]

specific_ticket_urlpatterns = [
    path("", event_views.EventTicketDetailView.as_view(), name='event_ticket_detail'),
    path("cancel/", login_required(event_views.EventTicketCancelView.as_view()), name='event_ticket_cancel'),
]
ticket_urlpatterns = [
    path("<uuid:pk>/", include(specific_ticket_urlpatterns)),
    path("me/", event_views.EventTicketMyListView.as_view(), name='event_ticket_my_list'),
]

urlpatterns = [
    path("articles/", include(article_urlpatterns)),
    path("events/", include(event_urlpatterns)),
    path("tickets/", include(ticket_urlpatterns)),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_article_adminpatterns = [
    path("change/", article_views.ArticleUpdateView.as_view(), name='article_update'),
    path("delete/", article_views.ArticleDeleteView.as_view(), name='article_delete'),
]
article_adminpatterns = [
    path("", article_views.AdminArticleListView.as_view(), name='admin_article_list'),
    path("add/", article_views.ArticleCreateView.as_view(), name='article_create'),
    path("<int:pk>/", include(specific_article_adminpatterns)),
]

specific_time_place_adminpatterns = [
    path("change/", event_views.TimePlaceUpdateView.as_view(), name='time_place_update'),
    path("duplicate/", event_views.TimePlaceDuplicateCreateView.as_view(), name='time_place_duplicate_create'),
    path("delete/", event_views.TimePlaceDeleteView.as_view(), name='time_place_delete'),
    path("tickets/", event_views.AdminTimePlaceTicketListView.as_view(), name='admin_time_place_ticket_list'),
]
time_place_adminpatterns = [
    path("add/", event_views.TimePlaceCreateView.as_view(), name='time_place_create'),
    path("<int:time_place_pk>/", include(specific_time_place_adminpatterns)),
]
specific_event_adminpatterns = [
    path("", event_views.AdminEventDetailView.as_view(), name='admin_event_detail'),
    path("change/", event_views.EventUpdateView.as_view(), name='event_update'),
    path("delete/", event_views.EventDeleteView.as_view(), name='event_delete'),
    path("tickets/", event_views.AdminEventTicketListView.as_view(), name='admin_event_ticket_list'),
    path("timeplaces/", include(time_place_adminpatterns)),
]
event_adminpatterns = [
    path("", event_views.AdminEventListView.as_view(), name='admin_event_list'),
    path("add/", event_views.EventCreateView.as_view(), name='event_create'),
    path("<int:pk>/", include(specific_event_adminpatterns)),
    path("participants/search/", event_views.AdminEventParticipantsSearchView.as_view(), name='admin_event_participants_search'),
]

adminpatterns = [
    path("articles/", include(article_adminpatterns)),
    path("events/", include(event_adminpatterns)),
]

# --- Admin API URL patterns (imported in `web/urls.py`) ---

article_adminapipatterns = [
    path("<int:pk>/toggle/", api_views.AdminAPIArticleToggleView.as_view(), name='admin_api_article_toggle'),
]

specific_event_adminapipatterns = [
    path("toggle/", api_views.AdminAPIEventToggleView.as_view(), name='admin_api_event_toggle'),
    path("timeplaces/<int:time_place_pk>/toggle/", api_views.AdminAPITimePlaceToggleView.as_view(), name='admin_api_time_place_toggle'),
]
event_adminapipatterns = [
    path("<int:pk>/", include(specific_event_adminapipatterns)),
]

adminapipatterns = [
    path("articles/", include(article_adminapipatterns)),
    path("events/", include(event_adminapipatterns)),
]
