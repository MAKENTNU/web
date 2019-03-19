from django.urls import path, register_converter

from tools import views

urlpatterns = [
    path(r'', views.ViewToolsView.as_view(), name='tools'),
    path(r'<int:pk>/', views.ViewToolView.as_view(), name='tools'),
    path(r'admin', views.ViewAdminView.as_view(), name='tools/admin'),
    path(r'admin/create', views.ViewAdminCreateView.as_view(), name='tools/create'),
    path(r'admin/<int:pk>/edit', views.ViewAdminEditView.as_view(), name='tools/edit'),
    path(r'admin/<int:pk>/delete', views.ViewDeleteView.as_view(), name='tools/delete'),
]