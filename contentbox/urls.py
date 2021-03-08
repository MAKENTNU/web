from django.urls import path

from contentbox.views import EditContentBoxView


urlpatterns = [
    path('<int:pk>/edit/', EditContentBoxView.as_view(), name='contentbox_edit'),
]
