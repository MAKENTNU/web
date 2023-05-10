from django.urls import path

from . import views


urlpatterns = [
    path("", views.CommitteeListView.as_view(), name='committee_list'),
    path("<int:pk>/", views.CommitteeDetailView.as_view(), name='committee_detail'),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

adminpatterns = [
    path("", views.AdminCommitteeListView.as_view(), name='admin_committee_list'),
    path("<int:pk>/change/", views.CommitteeUpdateView.as_view(), name='committee_update'),
]
