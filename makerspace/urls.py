from django.contrib.auth.decorators import login_required
from django.urls import path

from contentbox.views import DisplayContentBoxView
from . import views


urlpatterns = [
    path("", views.MakerspaceView.as_view(), name='makerspace'),
    path("equipment/", views.EquipmentListView.as_view(), name='makerspace_equipment_list'),
    path("equipment/admin/", login_required(views.AdminEquipmentListView.as_view()), name='makerspace_admin_equipment_list'),
    path("equipment/admin/create/", login_required(views.CreateEquipmentView.as_view()), name='makerspace_equipment_create'),
    path("equipment/admin/<int:pk>/edit/", login_required(views.EditEquipmentView.as_view()), name='makerspace_equipment_edit'),
    path("equipment/admin/<int:pk>/delete/", login_required(views.DeleteEquipmentView.as_view()), name='makerspace_equipment_delete'),
    path("equipment/<int:pk>/", views.EquipmentDetailView.as_view(), name='makerspace_equipment_detail'),
    DisplayContentBoxView.get_path('rules'),
]
