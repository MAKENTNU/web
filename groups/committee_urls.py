from django.conf.urls import url

from .views import CommitteeList


urlpatterns = [
    url('^$', CommitteeList.as_view(), name='committee_list'),
]
