from django.urls import path

from .views import CommitteeList

urlpatterns = [
    path('', CommitteeList.as_view(), name='committee_list'),
]
