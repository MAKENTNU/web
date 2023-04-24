from django.urls import include, path

from . import views


urlpatterns = [
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_announcement_adminpatterns = [
    path("change/", views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path("delete/", views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
]

adminpatterns = [
    path("", views.AdminAnnouncementListView.as_view(), name='admin_announcement_list'),
    path("add/", views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path("<int:pk>/", include(specific_announcement_adminpatterns)),
]
