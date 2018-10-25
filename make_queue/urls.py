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
    #path('<machine:machine>/<%Y/%m/%d:date>', api.reservation.get_reservations_day_and_machine, name="reservation_json"),
    #path('<reservation:reservation>/', api.reservation.get_future_reservations_machine_without_specific_reservation, name="reservation_json"),
]

quota_url_patterns = [
    path('json/<machine_type:machine_type>/', login_required(api.quota.get_user_quota_max_length)),
    path('update/3D-printer/', permission_required("make_queue.can_edit_quota", raise_exception=True)(api.quota.UpdateQuota3D.as_view())),
    path('update/allowed/', csrf_exempt(api.quota.UpdateAllowed.as_view()), name="update_allowed_3D_printer"),
    path('update/sewing/', permission_required("make_queue.can_edit_quota", raise_exception=True)(api.quota.UpdateSewingQuota.as_view())),
    path('update/', permission_required("make_queue.can_edit_quota", raise_exception=True)(admin.quota.UpdatePrinterHandlerView.as_view()), name="update_printer_handler"),
    path('<username:user>/', permission_required("make_queue.can_edit_quota", raise_exception=True)(quota.user.GetUserQuotaView.as_view())),
    path('', permission_required("make_queue.can_edit_quota", raise_exception=True)(admin.quota.QuotaView.as_view()), name="quota_panel"),
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
