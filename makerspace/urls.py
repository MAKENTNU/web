from django.contrib.auth.decorators import login_required
from django.urls import path

from contentbox.views import DisplayContentBoxView
from . import views

urlpatterns = [
    path('equipment/', views.EquipmentListView.as_view(), name='makerspace-equipment-list'),
    path('equipment/admin/', login_required(views.AdminEquipmentView.as_view()), name='makerspace-equipment-admin'),
    path('equipment/admin/create/', login_required(views.CreateEquipmentView.as_view()), name='makerspace-equipment-create'),
    path('equipment/admin/<int:pk>/edit/', login_required(views.EditEquipmentView.as_view()), name='makerspace-equipment-edit'),
    path('equipment/admin/<int:pk>/delete/', login_required(views.DeleteEquipmentView.as_view()), name='makerspace-equipment-delete'),
    path('equipment/<int:pk>/', views.EquipmentView.as_view(), name='makerspace-equipment'),
    DisplayContentBoxView.get_path('rules'),
]
