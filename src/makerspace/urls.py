from django.contrib.auth.decorators import login_required
from django.urls import path

from contentbox.views import ContentBoxDetailView
from . import views


urlpatterns = [
    path("", views.MakerspaceView.as_view(url_name='makerspace'), name='makerspace'),
    path("equipment/", views.EquipmentListView.as_view(), name='equipment_list'),
    path("equipment/admin/", login_required(views.AdminEquipmentListView.as_view()), name='admin_equipment_list'),
    path("equipment/admin/create/", login_required(views.EquipmentCreateView.as_view()), name='equipment_create'),
    path("equipment/admin/<int:pk>/edit/", login_required(views.EquipmentUpdateView.as_view()), name='equipment_update'),
    path("equipment/admin/<int:pk>/delete/", login_required(views.EquipmentDeleteView.as_view()), name='equipment_delete'),
    path("equipment/<int:pk>/", views.EquipmentDetailView.as_view(), name='equipment_detail'),
    ContentBoxDetailView.get_path('rules'),
]
