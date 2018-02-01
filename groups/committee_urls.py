from django.conf.urls import url

from .views import CommitteeList


urlpatterns = [
    url('^$', CommitteeList.as_view()),
]
