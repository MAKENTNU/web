from django.urls import include, path

from contentbox.views import ContentBoxDetailView
from . import views


equipment_urlpatterns = [
    path("", views.EquipmentListView.as_view(), name='equipment_list'),
    path("<int:pk>/", views.EquipmentDetailView.as_view(), name='equipment_detail'),
]
urlpatterns = [
    path("", views.MakerspaceView.as_view(url_name='makerspace'), name='makerspace'),
    path("card-registration/", views.CardRegistrationView.as_view(), name='card_registration'),
    path("equipment/", include(equipment_urlpatterns)),
    ContentBoxDetailView.get_path('rules'),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_equipment_adminpatterns = [
    path("change/", views.EquipmentUpdateView.as_view(), name='equipment_update'),
    path("delete/", views.EquipmentDeleteView.as_view(), name='equipment_delete'),
]
equipment_adminpatterns = [
    path("", views.AdminEquipmentListView.as_view(), name='admin_equipment_list'),
    path("add/", views.EquipmentCreateView.as_view(), name='equipment_create'),
    path("<int:pk>/", include(specific_equipment_adminpatterns)),
]

adminpatterns = [
    path("equipment/", include(equipment_adminpatterns)),
]
