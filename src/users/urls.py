from django.urls import path

from .api import views as api_views


# --- Admin API URL patterns (imported in `web/urls.py`) ---

adminapipatterns = [
    path("username/<str:username>/", api_views.AdminAPIBasicUserInfoView.as_view(), name='admin_api_basic_user_info'),
]
