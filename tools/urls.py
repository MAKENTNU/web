from django.urls import path, register_converter

from tools.views import ViewToolsView, ViewToolView, ViewAdminWiev

urlpatterns = [
    path(r'', ViewToolsView.as_view(), name='tools'),
    path(r'<int:pk>/', ViewToolView.as_view(), name='tools'),
    path(r'admin', ViewAdminWiev.as_view(), name='tools/admin'),
]
