from django.urls import path

from . import views


urlpatterns = [
    path("<int:pk>/edit/", views.EditContentBoxView.as_view(), name='contentbox_edit'),
]
