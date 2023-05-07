from decorator_include import decorator_include
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from .api import views as api_views
from .views import (
    course as course_views, machine as machine_views, quota as quota_views, reservation as reservation_views,
    reservation_rule as reservation_rule_views,
)


specific_machinetype_urlpatterns = [
    path("reservationrules/", reservation_rule_views.ReservationRuleListView.as_view(), name='reservation_rule_list'),
    path("usagerules/", machine_views.MachineUsageRuleDetailView.as_view(), name='machine_usage_rule_detail'),
]

specific_machine_urlpatterns = [
    path("", machine_views.MachineDetailView.as_view(), name='machine_detail'),
    path("reservations/add/", login_required(reservation_views.ReservationCreateView.as_view()), name='reservation_create'),
]
machine_urlpatterns = [
    path("", machine_views.MachineListView.as_view(), name='machine_list'),
    path("<int:pk>/", include(specific_machine_urlpatterns)),
]

specific_reservation_urlpatterns = [
    path("change/", login_required(reservation_views.ReservationUpdateView.as_view()), name='reservation_update'),
]
reservation_urlpatterns = [
    path("", reservation_views.ReservationListView.as_view(), name='reservation_list'),
    path("<int:pk>/", include(specific_reservation_urlpatterns)),
    path("find-free-slots/", reservation_views.ReservationFindFreeSlotsView.as_view(), name='reservation_find_free_slots'),
]

urlpatterns = [
    path("machinetypes/<int:pk>/", include(specific_machinetype_urlpatterns)),
    path("machines/", include(machine_urlpatterns)),
    path("reservations/", include(reservation_urlpatterns)),
]

# --- API URL patterns (imported in `web/urls.py`) ---

specific_machinetype_apipatterns = [
    path("reservationrules/", api_views.APIReservationRuleListView.as_view(), name='api_reservation_rule_list'),
]

specific_machine_apipatterns = [
    path("data/", api_views.APIMachineDataView.as_view(), name='api_machine_data'),
    path("reservations/", api_views.APIReservationListView.as_view(), name='api_reservation_list'),
]

specific_reservation_apipatterns = [
    path("finish/", api_views.APIReservationMarkFinishedView.as_view(), name='api_reservation_mark_finished'),
    path("delete/", api_views.APIReservationDeleteView.as_view(), name='api_reservation_delete'),
]

apipatterns = [
    path("machinetypes/<int:pk>/", include(specific_machinetype_apipatterns)),
    path("machines/<int:pk>/", include(specific_machine_apipatterns)),
    path("reservations/<int:pk>/", decorator_include(login_required, specific_reservation_apipatterns)),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_reservation_rule_adminpatterns = [
    path("change/", reservation_rule_views.ReservationRuleUpdateView.as_view(), name='reservation_rule_update'),
    path("delete/", reservation_rule_views.ReservationRuleDeleteView.as_view(), name='reservation_rule_delete'),
]
reservation_rules_adminpatterns = [
    path("add/", reservation_rule_views.ReservationRuleCreateView.as_view(), name='reservation_rule_create'),
    path("<int:reservation_rule_pk>/", include(specific_reservation_rule_adminpatterns)),
]
specific_machinetype_adminpatterns = [
    path("reservationrules/", include(reservation_rules_adminpatterns)),
    path("usagerules/change/", machine_views.MachineUsageRuleUpdateView.as_view(), name='machine_usage_rule_update'),
]

specific_machine_adminpatterns = [
    path("change/", machine_views.MachineUpdateView.as_view(), name='machine_update'),
    path("delete/", machine_views.MachineDeleteView.as_view(), name='machine_delete'),
]
machine_adminpatterns = [
    path("add/", machine_views.MachineCreateView.as_view(), name='machine_create'),
    path("<int:pk>/", include(specific_machine_adminpatterns)),
]

specific_course_adminpatterns = [
    path("change/", course_views.Printer3DCourseUpdateView.as_view(), name='printer_3d_course_update'),
    path("delete/", course_views.Printer3DCourseDeleteView.as_view(), name='printer_3d_course_delete'),
]
course_adminpatterns = [
    path("", course_views.Printer3DCourseListView.as_view(), name='printer_3d_course_list'),
    path("add/", course_views.Printer3DCourseCreateView.as_view(), name='printer_3d_course_create'),
    path("<int:pk>/", include(specific_course_adminpatterns)),
    path("status/change/", course_views.Printer3DCourseStatusBulkUpdateView.as_view(), name='printer_3d_course_status_bulk_update'),
    path("download/xlsx/", course_views.Printer3DCourseXLSXView.as_view(), name='printer_3d_course_xlsx'),
]

specific_quota_adminpatterns = [
    path("change/", quota_views.QuotaUpdateView.as_view(), name='quota_update'),
    path("delete/", quota_views.QuotaDeleteView.as_view(), name='quota_delete'),
]
quota_adminpatterns = [
    path("", quota_views.AdminQuotaPanelView.as_view(), name='admin_quota_panel'),
    path("add/", quota_views.QuotaCreateView.as_view(), name='quota_create'),
    path("<int:pk>/", include(specific_quota_adminpatterns)),
    path("users/<int:pk>/", quota_views.AdminUserQuotaListView.as_view(), name='admin_user_quota_list'),
]

adminpatterns = [
    path("machinetypes/<int:pk>/", include(specific_machinetype_adminpatterns)),
    path("machines/", include(machine_adminpatterns)),
    path("courses/", include(course_adminpatterns)),
    path("quotas/", include(quota_adminpatterns)),
]
