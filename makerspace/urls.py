from django.urls import path, register_converter

from makerspace import views

urlpatterns = [
    path('', views.ViewMakerspaceView.as_view(), name='makerspace'),
    path(r'<int:pk>/edit/', views.ViewAdminMakerspaceView.as_view(), name='makerspace/edit'),
    path(r'tools/', views.ViewToolsView.as_view(), name='makerspace/tools'),
    path(r'<int:pk>/', views.ViewToolView.as_view(), name='makerspace'),
    path(r'tools/admin', views.ViewAdminView.as_view(), name='makerspace/tools/admin'),
    path(r'tools/admin/create', views.ViewAdminCreateView.as_view(), name='makerspace/tools/create'),
    path(r'tools/admin/<int:pk>/edit', views.ViewAdminEditView.as_view(), name='makerspace/tools/edit'),
    path(r'tools/admin/<int:pk>/delete', views.ViewDeleteView.as_view(), name='makerspace/tools/delete'),
]