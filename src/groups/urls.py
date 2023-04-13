from django.urls import path

from . import views


urlpatterns = [
    path("", views.CommitteeListView.as_view(), name='committee_list'),
    path("<int:pk>/", views.CommitteeDetailView.as_view(), name='committee_detail'),
    path("<int:pk>/edit/", views.CommitteeUpdateView.as_view(), name='committee_edit'),
    path("admin/", views.AdminCommitteeListView.as_view(), name='committee_admin'),
]
