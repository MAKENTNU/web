from django.urls import path
from django.contrib.auth.decorators import login_required
from makerspace.views import ViewMakerspaceView, EditMakerspaceView, \
    ToolsView, ToolView, EditToolView, CreateToolView, \
    AdminToolView, DeleteToolView


urlpatterns = [
    path('', ViewMakerspaceView.as_view(), name='makerspace'),
    path('admin/<int:pk>/edit/', login_required(EditMakerspaceView.as_view()), name='makerspace-edit'),
    path('tools/', ToolsView.as_view(), name='makerspace-tools'),
    path('tools/admin', login_required(AdminToolView.as_view()), name='makerspace-tools-admin'),
    path('tools/admin/create', login_required(CreateToolView.as_view()), name='makerspace-tools-create'),
    path('tools/admin/<int:pk>/edit', login_required(EditToolView.as_view()), name='makerspace-tools-edit'),
    path('tools/admin/<int:pk>/delete', login_required(DeleteToolView.as_view()), name='makerspace-tools-delete'),
    path('tool/<int:pk>/', ToolView.as_view(), name='makerspace-tool'),
]
