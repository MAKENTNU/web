from django.conf.urls import url, include
from django.contrib import admin

from checkin.views import CheckInView, ViewSkillsView

urlpatterns = [
    url(r'^$', ViewSkillsView.as_view()),
    url(r'^post/$', CheckInView.as_view()),
]