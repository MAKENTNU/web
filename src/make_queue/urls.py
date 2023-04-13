from django.contrib.auth.decorators import login_required
from django.urls import include, path, register_converter

from . import converters
from .views.admin import course, quota, reservation as reservation_admin
from .views.api import calendar as calendar_api, reservation as reservation_api, user_info
from .views.quota import user
from .views.reservation import calendar, machine, reservation, rules


register_converter(converters.Year, 'year')
register_converter(converters.Week, 'week')

machine_urlpatterns = [
    path("create/", machine.MachineCreateView.as_view(), name='machine_create'),
    path("<int:pk>/", calendar.MachineDetailView.as_view(redirect_to_current_week=True), name='machine_detail'),
    path("<int:pk>/edit/", machine.MachineUpdateView.as_view(), name='machine_update'),
    path("<int:pk>/delete/", machine.MachineDeleteView.as_view(), name='machine_delete'),
]

calendar_urlpatterns = [
    path("<int:pk>/reservations/", calendar_api.APIReservationListView.as_view(), name='api_reservation_list'),
    path("<int:pk>/rules/", calendar_api.APIReservationRuleListView.as_view(), name='api_reservation_rule_list'),
]

json_urlpatterns = [
    path("<int:pk>/", login_required(reservation_api.APIMachineDataView.as_view()), name='api_machine_data'),
    path("<int:pk>/<int:reservation_pk>/", login_required(reservation_api.APIMachineDataView.as_view()), name='api_machine_data'),
    path("<str:username>/", user_info.AdminAPIBasicUserInfoView.as_view(), name='admin_api_basic_user_info'),
]

rules_urlpatterns = [
    path("", rules.ReservationRuleListView.as_view(), name='reservation_rule_list'),
    path("create/", rules.ReservationRuleCreateView.as_view(), name='reservation_rule_create'),
    path("<int:reservation_rule_pk>/edit/", rules.ReservationRuleUpdateView.as_view(), name='reservation_rule_update'),
    path("<int:reservation_rule_pk>/delete/", rules.ReservationRuleDeleteView.as_view(), name='reservation_rule_delete'),
    path("usage/", rules.MachineUsageRuleDetailView.as_view(), name='machine_usage_rule_detail'),
    path("usage/edit/", rules.MachineUsageRuleUpdateView.as_view(), name='machine_usage_rule_update'),
]

specific_machinetype_urlpatterns = [
    path("rules/", include(rules_urlpatterns)),
]

quota_urlpatterns = [
    path("", quota.AdminQuotaPanelView.as_view(), name='admin_quota_panel'),
    path("create/", quota.QuotaCreateView.as_view(), name='quota_create'),
    path("<int:pk>/update/", quota.QuotaUpdateView.as_view(), name='quota_update'),
    path("<int:pk>/delete/", quota.QuotaDeleteView.as_view(), name='quota_delete'),
    path("user/<int:pk>/", user.AdminUserQuotaListView.as_view(), name='admin_user_quota_list'),
    path("<int:pk>/", quota.AdminQuotaPanelView.as_view(), name='admin_quota_panel'),
]

course_urlpatterns = [
    path("", course.Printer3DCourseListView.as_view(), name='printer_3d_course_list'),
    path("status/", course.Printer3DCourseStatusBulkUpdateView.as_view(), name='printer_3d_course_status_bulk_update'),
    path("download/", course.Printer3DCourseXLSXView.as_view(), name='printer_3d_course_xlsx'),
    path("create/", course.Printer3DCourseCreateView.as_view(), name='printer_3d_course_create'),
    path("<int:pk>/edit/", course.Printer3DCourseUpdateView.as_view(), name='printer_3d_course_update'),
    path("<int:pk>/delete/", course.Printer3DCourseDeleteView.as_view(), name='printer_3d_course_delete'),
]

urlpatterns = [
    path("", machine.MachineListView.as_view(), name='machine_list'),
    path("machines/", include(machine_urlpatterns)),
    path("<year:year>/<week:week>/<int:pk>/", calendar.MachineDetailView.as_view(), name='machine_detail'),
    path("calendar/", include(calendar_urlpatterns)),
    path("json/", include(json_urlpatterns)),
    path("create/<int:pk>/", login_required(reservation.ReservationCreateView.as_view()), name='reservation_create'),
    path("<int:reservation_pk>/edit/", login_required(reservation.ReservationUpdateView.as_view()), name='reservation_update'),
    path("<int:pk>/finish/", login_required(reservation.APIReservationMarkFinishedView.as_view()), name='api_reservation_mark_finished'),
    path("<int:pk>/", login_required(reservation.APIReservationDeleteView.as_view()), name='api_reservation_delete'),
    path("me/", reservation.ReservationMyListView.as_view(), name='reservation_my_list'),
    path("admin/", reservation_admin.AdminReservationMAKEListView.as_view(), name='admin_reservation_MAKE_list'),
    path("slot/", reservation.ReservationFindFreeSlotsView.as_view(), name='reservation_find_free_slots'),
    path("machinetypes/<int:pk>/", include(specific_machinetype_urlpatterns)),
    path("quota/", include(quota_urlpatterns)),
    path("course/", include(course_urlpatterns)),
]
