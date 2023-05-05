from django.urls import path

from . import views


urlpatterns = [
    path("", views.CommitteeListView.as_view(), name='committee_list'),
    path("<int:pk>/", views.CommitteeDetailView.as_view(), name='committee_detail'),
    path("<int:pk>/change/", views.CommitteeUpdateView.as_view(), name='committee_update'),
    path("admin/", views.AdminCommitteeListView.as_view(), name='admin_committee_list'),
]
