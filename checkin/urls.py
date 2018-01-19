from django.conf.urls import url, include
from django.contrib import admin

from checkin.views import TemporaryView

urlpatterns = [
    url(r'^', TemporaryView.as_view())
]