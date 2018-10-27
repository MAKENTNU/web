from django.urls import include, path, register_converter, re_path
from django.views.decorators.csrf import csrf_exempt

from make_queue.views import api, admin, quota, reservation
from . import converters
from django.contrib.auth.decorators import login_required, permission_required

register_converter(converters.MachineType, "machine_type")
register_converter(converters.SpecificMachine, "machine")
register_converter(converters.MachineReservation, "reservation")
register_converter(converters.UserByUsername, "username")
register_converter(converters.Date, "%Y/%m/%d")
register_converter(converters.Year, "year")
register_converter(converters.Week, "week")
register_converter(converters.DateTime, "time")

json_urlpatterns = [
    path('<machine:machine>', login_required(api.reservation.get_machine_data), name="reservation_json"),
    path('<machine:machine>/<reservation:reservation>/', api.reservation.get_machine_data, name="reservation_json"),
]

quota_url_patterns = [
    path('create/', permission_required("make_queue.add_quota")(admin.quota.CreateQuotaView.as_view()), name="create_quota"),
    path('update/<int:pk>/', permission_required("make_queue.update_quota")(admin.quota.EditQuotaView.as_view()), name="edit_quota"),
    path('delete/<int:pk>/', permission_required("make_queue.delete_quota")(admin.quota.DeleteQuotaView.as_view()), name="delete_quota"),
    path('user/<username:user>/', permission_required("make_queue.update_quota", raise_exception=True)(quota.user.GetUserQuotaView.as_view()), name="quotas_user"),
    path('<username:user>/', permission_required("make_queue.update_quota", raise_exception=True)(admin.quota.QuotaView.as_view()), name="quota_panel"),
    path('', permission_required("make_queue.update_quota", raise_exception=True)(admin.quota.QuotaView.as_view()), name="quota_panel"),
]

rules_url_patterns = [
    path('<machine_type:machine_type>/', reservation.rules.RulesOverviewView.as_view(), name="machine_rules"),
    path('usage/edit/<int:pk>/', reservation.rules.EditUsageRulesView.as_view(), name="edit_machine_usage_rules"),
    path('usage/<machine_type:machine_type>/', reservation.rules.MachineUsageRulesView.as_view(), name="machine_usage_rules"),
    path('delete/<int:pk>/', reservation.rules.DeleteReservationRules.as_view(), name="delete_machine_rule"),
    path('create/', reservation.rules.CreateReservationRuleView.as_view(), name="create_machine_rule"),
    path('edit/<int:pk>/', reservation.rules.EditReservationRuleView.as_view(), name="edit_machine_rule"),
]

urlpatterns = [
    path('<year:year>/<week:week>/<machine:machine>', reservation.calendar.ReservationCalendarView.as_view(), name="reservation_calendar"),
    path('calendar/<year:year>/<week:week>/<machine:machine>/', reservation.calendar.ReservationCalendarComponentView.as_view(), name="reservation_calendar_component"),
    path('make/<machine:machine>/', login_required(reservation.reservation.MakeReservationView.as_view()), name="make_reservation"),
    path('make/<time:start_time>/<machine:machine>/', login_required(reservation.reservation.MakeReservationView.as_view()), name="make_reservation"),
    path('me/', login_required(reservation.overview.MyReservationsView.as_view()), name="my_reservations"),
    path('admin/', permission_required('make_queue.can_create_event_reservation', raise_exception=True)(admin.reservation.AdminReservationView.as_view()), name="admin_reservation"),
    path('delete/', login_required(reservation.reservation.DeleteReservationView.as_view()), name="delete_reservation"),
    path('change/<reservation:reservation>/', login_required(reservation.reservation.ChangeReservationView.as_view()), name="change_reservation"),
    path('rules/', include(rules_url_patterns)),
    path('json/', include(json_urlpatterns)),
    path('quota/', include(quota_url_patterns)),
    re_path('^', reservation.machine.MachineView.as_view(), name="reservation_machines_overview")
]
