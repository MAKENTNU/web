from django.urls import path

from .views import CommitteeList, EditCommitteeView, CommitteeDetailView, CommitteeAdminView

urlpatterns = [
    path('', CommitteeList.as_view(), name='committee_list'),
    path('<int:pk>/edit', EditCommitteeView.as_view(), name='committee_edit'),
    path('<int:pk>/', CommitteeDetailView.as_view(), name='committee_detail'),
    path('admin/', CommitteeAdminView.as_view(), name='committee_admin'),
]
