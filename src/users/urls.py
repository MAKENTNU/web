from django.urls import path

from . import views


urlpatterns = [
    path("username/<str:username>/", views.AdminAPIBasicUserInfoView.as_view(), name='admin_api_basic_user_info'),
]
