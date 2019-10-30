from django.urls import path, register_converter

from makerspace import views

urlpatterns = [
    path('', views.ViewMakerspaceView.as_view(), name='makerspace'),
    path(r'tools/', views.ViewToolsView.as_view(), name='makerspace/tools'),
    path(r'<int:pk>/', views.ViewToolView.as_view(), name='makerspace'),
    path(r'admin', views.ViewAdminView.as_view(), name='makerspace/admin'),
    path(r'admin/create', views.ViewAdminCreateView.as_view(), name='makerspace/create'),
    path(r'admin/<int:pk>/edit', views.ViewAdminEditView.as_view(), name='makerspace/edit'),
    path(r'admin/<int:pk>/delete', views.ViewDeleteView.as_view(), name='makerspace/delete'),
]