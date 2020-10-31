from django.contrib.auth.decorators import login_required, permission_required
from django.urls import include, path, register_converter, re_path

from make_queue.views import api, admin, quota, reservation
from . import converters

register_converter(converters.SpecificMachineType, "machine_type")
register_converter(converters.SpecificMachine, "machine")
register_converter(converters.MachineReservation, "reservation")
register_converter(converters.UserByUsername, "username")
register_converter(converters.Date, "%Y/%m/%d")
register_converter(converters.Year, "year")
register_converter(converters.Week, "week")
register_converter(converters.DateTime, "time")

machine_url_patterns = [
    path('create/', permission_required("make_queue.add_machine")(reservation.machine.CreateMachineView.as_view()), name="create_machine"),
    path('edit/<int:pk>/', permission_required("make_queue.change_machine")(reservation.machine.EditMachineView.as_view()), name="edit_machine"),
    path('delete/<int:pk>/', permission_required("make_queue.delete_machine")(reservation.machine.DeleteMachineView.as_view()),
         name="delete_machine"),
]

calendar_url_patterns = [
    path('<machine:machine>/reservations', api.calendar.get_reservations, name="api_reservations"),
    path('<machine:machine>/rules', api.calendar.get_reservation_rules, name="api_reservation_rules"),
]

json_urlpatterns = [
    path('<machine:machine>', login_required(api.reservation.get_machine_data), name="reservation_json"),
    path('<machine:machine>/<reservation:reservation>/', api.reservation.get_machine_data, name="reservation_json"),
    path('<str:username>/', permission_required("make_queue.add_printer3dcourse")(api.user_info.get_user_info_from_username), name="user_json"),
]

rules_url_patterns = [
    path('<machine_type:machine_type>/', reservation.rules.RulesOverviewView.as_view(), name="machine_rules"),
    path('create/', reservation.rules.CreateReservationRuleView.as_view(), name="create_machine_rule"),
    path('edit/<int:pk>/', reservation.rules.EditReservationRuleView.as_view(), name="edit_machine_rule"),
    path('delete/<int:pk>/', reservation.rules.DeleteReservationRules.as_view(), name="delete_machine_rule"),
    path('usage/<machine_type:machine_type>/', reservation.rules.MachineUsageRulesView.as_view(), name="machine_usage_rules"),
    path('usage/edit/<int:pk>/', reservation.rules.EditUsageRulesView.as_view(), name="edit_machine_usage_rules"),
]

quota_url_patterns = [
    path('', permission_required("make_queue.change_quota", raise_exception=True)(admin.quota.QuotaView.as_view()), name="quota_panel"),
    path('create/', permission_required("make_queue.add_quota")(admin.quota.CreateQuotaView.as_view()), name="create_quota"),
    path('update/<int:pk>/', permission_required("make_queue.change_quota")(admin.quota.EditQuotaView.as_view()), name="edit_quota"),
    path('delete/<int:pk>/', permission_required("make_queue.delete_quota")(admin.quota.DeleteQuotaView.as_view()), name="delete_quota"),
    path('user/<username:user>/', permission_required("make_queue.change_quota", raise_exception=True)(quota.user.GetUserQuotaView.as_view()),
         name="quotas_user"),
    path('<username:user>/', permission_required("make_queue.change_quota", raise_exception=True)(admin.quota.QuotaView.as_view()),
         name="quota_panel"),
]

course_url_patterns = [
    path('', permission_required("make_queue.change_printer3dcourse")(admin.course.CourseView.as_view()), name="course_panel"),
    path('status/', permission_required("make_queue.change_printer3dcourse")(admin.course.BulkStatusUpdate.as_view()), name="bulk_status_update"),
    path('download/', permission_required("make_queue.change_printer3dcourse")(admin.course.CourseXLSXView.as_view()),
         name="download_course_registrations"),
    path('create/', permission_required("make_queue.add_printer3dcourse")(admin.course.CreateRegistrationView.as_view()),
         name="create_course_registration"),
    path('create/success/', permission_required("make_queue.add_printer3dcourse")(admin.course.CreateRegistrationView.as_view(is_next=True)),
         name="create_course_registration_success"),
    path('edit/<int:pk>/', permission_required("make_queue.change_printer3dcourse")(admin.course.EditRegistrationView.as_view()),
         name="edit_course_registration"),
    path('delete/<int:pk>/', permission_required("make_queue.delete_printer3dcourse")(admin.course.DeleteRegistrationView.as_view()),
         name="delete_course_registration"),
]

urlpatterns = [
    re_path('^', reservation.machine.MachineView.as_view(), name="reservation_machines_overview"),
    path('machine/', include(machine_url_patterns)),
    path('<year:year>/<week:week>/<machine:machine>', reservation.calendar.ReservationCalendarView.as_view(), name="reservation_calendar"),
    path('calendar/', include(calendar_url_patterns)),
    path('json/', include(json_urlpatterns)),
    path('create/<machine:machine>/', login_required(reservation.reservation.CreateReservationView.as_view()), name="create_reservation"),
    path('change/<reservation:reservation>/', login_required(reservation.reservation.ChangeReservationView.as_view()), name="change_reservation"),
    path('finish/', login_required(reservation.reservation.MarkReservationAsDone.as_view()), name="mark_reservation_done"),
    path('delete/', login_required(reservation.reservation.DeleteReservationView.as_view()), name="delete_reservation"),
    path('me/', login_required(reservation.overview.MyReservationsView.as_view()), name="my_reservations"),
    path('admin/',
         permission_required('make_queue.can_create_event_reservation', raise_exception=True)(admin.reservation.AdminReservationView.as_view()),
         name="admin_reservation"),
    path('slot/', reservation.reservation.FindFreeSlot.as_view(), name="find_free_slot"),
    path('rules/', include(rules_url_patterns)),
    path('quota/', include(quota_url_patterns)),
    path('course/', include(course_url_patterns)),
]
