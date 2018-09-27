from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from tools.views import ToolView

urlpatterns = [
    url(r'^$', ToolView.as_view()),
]
