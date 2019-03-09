from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include

from internal.views import Home

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("", Home.as_view(), name="home"),
    prefix_default_language=False
)
