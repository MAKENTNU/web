from django.contrib.auth.decorators import login_required, permission_required
from django.urls import include, path, register_converter

from . import converters
from .views import admin, api, quota, reservation


register_converter(converters.Year, 'year')
register_converter(converters.Week, 'week')

machine_urlpatterns = [
    path("create/", permission_required('make_queue.add_machine')(reservation.machine.CreateMachineView.as_view()), name='create_machine'),
    path("<int:pk>/edit/", permission_required('make_queue.change_machine')(reservation.machine.EditMachineView.as_view()), name='edit_machine'),
    path("<int:pk>/delete/", permission_required('make_queue.delete_machine')(reservation.machine.DeleteMachineView.as_view()),
         name='delete_machine'),
]

calendar_urlpatterns = [
    path("<int:pk>/reservations/", api.calendar.APIReservationListView.as_view(), name='api_reservations'),
    path("<int:pk>/rules/", api.calendar.APIReservationRuleListView.as_view(), name='api_reservation_rules'),
]

json_urlpatterns = [
    path("<int:pk>/", login_required(api.reservation.APIMachineDataView.as_view()), name='reservation_json'),
    path("<int:pk>/<int:reservation_pk>/", login_required(api.reservation.APIMachineDataView.as_view()), name='reservation_json'),
    path("<str:username>/", permission_required('make_queue.add_printer3dcourse')(api.user_info.get_user_info_from_username), name='user_json'),
]

rules_urlpatterns = [
    path("", reservation.rules.ReservationRuleListView.as_view(), name='reservation_rule_list'),
    path("create/", reservation.rules.CreateReservationRuleView.as_view(), name='create_reservation_rule'),
    path("<int:reservation_rule_pk>/edit/", reservation.rules.EditReservationRuleView.as_view(), name='edit_reservation_rule'),
    path("<int:reservation_rule_pk>/delete/", reservation.rules.DeleteReservationRuleView.as_view(), name='delete_reservation_rule'),
    path("usage/", reservation.rules.MachineUsageRulesDetailView.as_view(), name='machine_usage_rules_detail'),
    path("usage/edit/", reservation.rules.EditUsageRulesView.as_view(), name='edit_machine_usage_rules'),
]

specific_machinetype_urlpatterns = [
    path("rules/", include(rules_urlpatterns)),
]

quota_urlpatterns = [
    path("", permission_required('make_queue.change_quota', raise_exception=True)(admin.quota.QuotaPanelView.as_view()), name='quota_panel'),
    path("create/", permission_required('make_queue.add_quota')(admin.quota.CreateQuotaView.as_view()), name='create_quota'),
    path("<int:pk>/update/", permission_required('make_queue.change_quota')(admin.quota.EditQuotaView.as_view()), name='edit_quota'),
    path("<int:pk>/delete/", permission_required('make_queue.delete_quota')(admin.quota.DeleteQuotaView.as_view()), name='delete_quota'),
    path("user/<int:pk>/", permission_required('make_queue.change_quota', raise_exception=True)(quota.user.UserQuotaListView.as_view()),
         name='user_quota_list'),
    path("<int:pk>/", permission_required('make_queue.change_quota', raise_exception=True)(admin.quota.QuotaPanelView.as_view()),
         name='quota_panel'),
]

course_urlpatterns = [
    path("", permission_required('make_queue.change_printer3dcourse')(admin.course.Printer3DCourseListView.as_view()),
         name='course_registration_list'),
    path("status/", permission_required('make_queue.change_printer3dcourse')(admin.course.BulkStatusUpdate.as_view()), name='bulk_status_update'),
    path("download/", permission_required('make_queue.change_printer3dcourse')(admin.course.CourseXLSXView.as_view()),
         name='download_course_registrations'),
    path("create/", permission_required('make_queue.add_printer3dcourse')(admin.course.CreateCourseRegistrationView.as_view()),
         name='create_course_registration'),
    path("create/success/", permission_required('make_queue.add_printer3dcourse')(admin.course.CreateCourseRegistrationView.as_view(is_next=True)),
         name='create_course_registration_success'),
    path("<int:pk>/edit/", permission_required('make_queue.change_printer3dcourse')(admin.course.EditCourseRegistrationView.as_view()),
         name='edit_course_registration'),
    path("<int:pk>/delete/", permission_required('make_queue.delete_printer3dcourse')(admin.course.DeleteCourseRegistrationView.as_view()),
         name='delete_course_registration'),
]

urlpatterns = [
    path("", reservation.machine.MachineListView.as_view(), name='machine_list'),
    path("machine/", include(machine_urlpatterns)),
    path("<year:year>/<week:week>/<int:pk>/", reservation.calendar.MachineDetailView.as_view(), name='machine_detail'),
    path("calendar/", include(calendar_urlpatterns)),
    path("json/", include(json_urlpatterns)),
    path("create/<int:pk>/", login_required(reservation.reservation.CreateReservationView.as_view()), name='create_reservation'),
    path("<int:reservation_pk>/edit/", login_required(reservation.reservation.EditReservationView.as_view()), name='edit_reservation'),
    path("<int:pk>/finish/", login_required(reservation.reservation.MarkReservationFinishedView.as_view()), name='mark_reservation_finished'),
    path("<int:pk>/", login_required(reservation.reservation.DeleteReservationView.as_view()), name='delete_reservation'),
    path("me/", reservation.reservation.MyReservationsListView.as_view(), name='my_reservations_list'),
    path("admin/",
         permission_required('make_queue.can_create_event_reservation', raise_exception=True)(admin.reservation.MAKEReservationsListView.as_view()),
         name='MAKE_reservations_list'),
    path("slot/", reservation.reservation.FindFreeSlotView.as_view(), name='find_free_slot'),
    path("machinetypes/<int:pk>/", include(specific_machinetype_urlpatterns)),
    path("quota/", include(quota_urlpatterns)),
    path("course/", include(course_urlpatterns)),
]
