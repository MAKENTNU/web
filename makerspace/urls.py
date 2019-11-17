from django.urls import path

from makerspace.views import ViewMakerspaceView, ViewAdminMakerspaceView, \
    ViewToolsView, ViewToolView, ViewAdminEditView, ViewAdminCreateView, \
    ViewAdminView, ViewDeleteView


urlpatterns = [
    path('', ViewMakerspaceView.as_view(), name='makerspace'),
    path(r'<int:pk>/edit/', ViewAdminMakerspaceView.as_view(), name='makerspace-edit'),
    path(r'tools/', ViewToolsView.as_view(), name='makerspace-tools'),
    path(r'tool/<int:pk>/', ViewToolView.as_view(), name='makerspace-tool'),
    path(r'tools/admin', ViewAdminView.as_view(), name='makerspace-tools-admin'),
    path(r'tools/admin/create', ViewAdminCreateView.as_view(), name='makerspace-tools-create'),
    path(r'tools/admin/<int:pk>/edit', ViewAdminEditView.as_view(), name='makerspace-tools-edit'),
    path(r'tools/admin/<int:pk>/delete', ViewDeleteView.as_view(), name='makerspace-tools-delete'),
]

