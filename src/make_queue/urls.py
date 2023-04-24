from decorator_include import decorator_include
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from .views.admin import course, quota
from .views.api import calendar as calendar_api, reservation as reservation_api
from .views.quota import user
from .views.reservation import calendar, machine, reservation, rules


specific_machinetype_urlpatterns = [
    path("reservationrules/", rules.ReservationRuleListView.as_view(), name='reservation_rule_list'),
    path("usagerules/", rules.MachineUsageRuleDetailView.as_view(), name='machine_usage_rule_detail'),
]

specific_machine_urlpatterns = [
    path("", calendar.MachineDetailView.as_view(), name='machine_detail'),
    path("reservations/add/", login_required(reservation.ReservationCreateView.as_view()), name='reservation_create'),
]
machine_urlpatterns = [
    path("", machine.MachineListView.as_view(), name='machine_list'),
    path("<int:pk>/", include(specific_machine_urlpatterns)),
]

specific_reservation_urlpatterns = [
    path("change/", login_required(reservation.ReservationUpdateView.as_view()), name='reservation_update'),
]
reservation_urlpatterns = [
    path("", reservation.ReservationListView.as_view(), name='reservation_list'),
    path("<int:pk>/", include(specific_reservation_urlpatterns)),
    path("find-free-slots/", reservation.ReservationFindFreeSlotsView.as_view(), name='reservation_find_free_slots'),
]

urlpatterns = [
    path("machinetypes/<int:pk>/", include(specific_machinetype_urlpatterns)),
    path("machines/", include(machine_urlpatterns)),
    path("reservations/", include(reservation_urlpatterns)),
]

# --- API URL patterns (imported in `web/urls.py`) ---

specific_machinetype_apipatterns = [
    path("reservationrules/", calendar_api.APIReservationRuleListView.as_view(), name='api_reservation_rule_list'),
]

specific_machine_apipatterns = [
    path("data/", reservation_api.APIMachineDataView.as_view(), name='api_machine_data'),
    path("reservations/", calendar_api.APIReservationListView.as_view(), name='api_reservation_list'),
]

specific_reservation_apipatterns = [
    path("finish/", reservation.APIReservationMarkFinishedView.as_view(), name='api_reservation_mark_finished'),
    path("delete/", reservation.APIReservationDeleteView.as_view(), name='api_reservation_delete'),
]

apipatterns = [
    path("machinetypes/<int:pk>/", include(specific_machinetype_apipatterns)),
    path("machines/<int:pk>/", include(specific_machine_apipatterns)),
    path("reservations/<int:pk>/", decorator_include(login_required, specific_reservation_apipatterns)),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_reservation_rule_adminpatterns = [
    path("change/", rules.ReservationRuleUpdateView.as_view(), name='reservation_rule_update'),
    path("delete/", rules.ReservationRuleDeleteView.as_view(), name='reservation_rule_delete'),
]
reservation_rules_adminpatterns = [
    path("add/", rules.ReservationRuleCreateView.as_view(), name='reservation_rule_create'),
    path("<int:reservation_rule_pk>/", include(specific_reservation_rule_adminpatterns)),
]
specific_machinetype_adminpatterns = [
    path("reservationrules/", include(reservation_rules_adminpatterns)),
    path("usagerules/change/", rules.MachineUsageRuleUpdateView.as_view(), name='machine_usage_rule_update'),
]

specific_machine_adminpatterns = [
    path("change/", machine.MachineUpdateView.as_view(), name='machine_update'),
    path("delete/", machine.MachineDeleteView.as_view(), name='machine_delete'),
]
machine_adminpatterns = [
    path("add/", machine.MachineCreateView.as_view(), name='machine_create'),
    path("<int:pk>/", include(specific_machine_adminpatterns)),
]

specific_course_adminpatterns = [
    path("change/", course.Printer3DCourseUpdateView.as_view(), name='printer_3d_course_update'),
    path("delete/", course.Printer3DCourseDeleteView.as_view(), name='printer_3d_course_delete'),
]
course_adminpatterns = [
    path("", course.Printer3DCourseListView.as_view(), name='printer_3d_course_list'),
    path("add/", course.Printer3DCourseCreateView.as_view(), name='printer_3d_course_create'),
    path("<int:pk>/", include(specific_course_adminpatterns)),
    path("status/change/", course.Printer3DCourseStatusBulkUpdateView.as_view(), name='printer_3d_course_status_bulk_update'),
    path("download/xlsx/", course.Printer3DCourseXLSXView.as_view(), name='printer_3d_course_xlsx'),
]

specific_quota_adminpatterns = [
    path("change/", quota.QuotaUpdateView.as_view(), name='quota_update'),
    path("delete/", quota.QuotaDeleteView.as_view(), name='quota_delete'),
]
quota_adminpatterns = [
    path("", quota.AdminQuotaPanelView.as_view(), name='admin_quota_panel'),
    path("add/", quota.QuotaCreateView.as_view(), name='quota_create'),
    path("<int:pk>/", include(specific_quota_adminpatterns)),
    path("users/<int:pk>/", user.AdminUserQuotaListView.as_view(), name='admin_user_quota_list'),
]

adminpatterns = [
    path("machinetypes/<int:pk>/", include(specific_machinetype_adminpatterns)),
    path("machines/", include(machine_adminpatterns)),
    path("courses/", include(course_adminpatterns)),
    path("quotas/", include(quota_adminpatterns)),
]
