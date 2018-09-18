from django.urls import path

from .views import CommitteeList, EditCommitteeView

urlpatterns = [
    path('', CommitteeList.as_view(), name='committee_list'),
    path('<int:pk>/edit', EditCommitteeView.as_view(), name='committee_edit'),
]
