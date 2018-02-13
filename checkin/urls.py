from django.conf.urls import url, include
from django.contrib import admin

from checkin.views import CheckInView, ShowSkillsView, ProfilePageView

urlpatterns = [
    url(r'^$', ShowSkillsView.as_view()),
    url(r'^profile$', ProfilePageView.as_view()),
    url(r'^post/$', CheckInView.as_view()),
]