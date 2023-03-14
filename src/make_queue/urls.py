from django.contrib.auth.decorators import login_required
from django.urls import include, path, register_converter

from util.url_utils import permission_required_else_denied
from . import converters
from .views.admin import course, quota, reservation as reservation_admin
from .views.api import calendar as calendar_api, reservation as reservation_api, user_info
from .views.quota import user
from .views.reservation import calendar, machine, reservation, rules


register_converter(converters.Year, 'year')
register_converter(converters.Week, 'week')

machine_urlpatterns = [
    path("create/", machine.CreateMachineView.as_view(), name='create_machine'),
    path("<int:pk>/", calendar.MachineDetailView.as_view(redirect_to_current_week=True), name='machine_detail'),
    path("<int:pk>/edit/", machine.EditMachineView.as_view(), name='edit_machine'),
    path("<int:pk>/delete/", machine.DeleteMachineView.as_view(), name='delete_machine'),
]

calendar_urlpatterns = [
    path("<int:pk>/reservations/", calendar_api.APIReservationListView.as_view(), name='api_reservations'),
    path("<int:pk>/rules/", calendar_api.APIReservationRuleListView.as_view(), name='api_reservation_rules'),
]

json_urlpatterns = [
    path("<int:pk>/", login_required(reservation_api.APIMachineDataView.as_view()), name='reservation_json'),
    path("<int:pk>/<int:reservation_pk>/", login_required(reservation_api.APIMachineDataView.as_view()), name='reservation_json'),
    path("<str:username>/", permission_required_else_denied('make_queue.add_printer3dcourse')(user_info.get_user_info_from_username),
         name='user_json'),
]

rules_urlpatterns = [
    path("", rules.ReservationRuleListView.as_view(), name='reservation_rule_list'),
    path("create/", rules.CreateReservationRuleView.as_view(), name='create_reservation_rule'),
    path("<int:reservation_rule_pk>/edit/", rules.EditReservationRuleView.as_view(), name='edit_reservation_rule'),
    path("<int:reservation_rule_pk>/delete/", rules.DeleteReservationRuleView.as_view(), name='delete_reservation_rule'),
    path("usage/", rules.MachineUsageRulesDetailView.as_view(), name='machine_usage_rules_detail'),
    path("usage/edit/", rules.EditUsageRulesView.as_view(), name='edit_machine_usage_rules'),
]

specific_machinetype_urlpatterns = [
    path("rules/", include(rules_urlpatterns)),
]

quota_urlpatterns = [
    path("", quota.QuotaPanelView.as_view(), name='quota_panel'),
    path("create/", quota.CreateQuotaView.as_view(), name='create_quota'),
    path("<int:pk>/update/", quota.EditQuotaView.as_view(), name='edit_quota'),
    path("<int:pk>/delete/", quota.DeleteQuotaView.as_view(), name='delete_quota'),
    path("user/<int:pk>/", user.UserQuotaListView.as_view(), name='user_quota_list'),
    path("<int:pk>/", quota.QuotaPanelView.as_view(), name='quota_panel'),
]

course_urlpatterns = [
    path("", course.Printer3DCourseListView.as_view(), name='course_registration_list'),
    path("status/", course.BulkStatusUpdate.as_view(), name='bulk_status_update'),
    path("download/", course.CourseXLSXView.as_view(), name='download_course_registrations'),
    path("create/", course.CreateCourseRegistrationView.as_view(), name='create_course_registration'),
    path("<int:pk>/edit/", course.EditCourseRegistrationView.as_view(), name='edit_course_registration'),
    path("<int:pk>/delete/", course.DeleteCourseRegistrationView.as_view(), name='delete_course_registration'),
]

urlpatterns = [
    path("", machine.MachineListView.as_view(), name='machine_list'),
    path("machines/", include(machine_urlpatterns)),
    path("<year:year>/<week:week>/<int:pk>/", calendar.MachineDetailView.as_view(), name='machine_detail'),
    path("calendar/", include(calendar_urlpatterns)),
    path("json/", include(json_urlpatterns)),
    path("create/<int:pk>/", login_required(reservation.CreateReservationView.as_view()), name='create_reservation'),
    path("<int:reservation_pk>/edit/", login_required(reservation.EditReservationView.as_view()), name='edit_reservation'),
    path("<int:pk>/finish/", login_required(reservation.MarkReservationFinishedView.as_view()), name='mark_reservation_finished'),
    path("<int:pk>/", login_required(reservation.DeleteReservationView.as_view()), name='delete_reservation'),
    path("me/", reservation.MyReservationsListView.as_view(), name='my_reservations_list'),
    path("admin/", reservation_admin.MAKEReservationsListView.as_view(), name='MAKE_reservations_list'),
    path("slot/", reservation.FindFreeSlotView.as_view(), name='find_free_slot'),
    path("machinetypes/<int:pk>/", include(specific_machinetype_urlpatterns)),
    path("quota/", include(quota_urlpatterns)),
    path("course/", include(course_urlpatterns)),
]
