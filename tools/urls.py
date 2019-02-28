from django.urls import path, register_converter

from tools import views

urlpatterns = [
    path(r'', views.ViewToolsView.as_view(), name='tools'),
    path(r'<int:pk>/', views.ViewToolView.as_view(), name='tools'),
    path(r'admin', views.ViewAdminWiev.as_view(), name='tools/admin'),
    path(r'admin/create', views.ViewAdminCreateVeiw.as_view(), name='tools/create'),
    path(r'admin/<int:pk>/edit', views.ViewAdminEditVeiw.as_view(), name='tools/edit'),

]
