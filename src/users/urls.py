from django.urls import path

from . import views


# --- Admin API URL patterns (imported in `web/urls.py`) ---

adminapipatterns = [
    path("username/<str:username>/", views.AdminAPIBasicUserInfoView.as_view(), name='admin_api_basic_user_info'),
]
