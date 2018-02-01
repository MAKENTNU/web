from django.urls import include, path, register_converter, re_path

from .views import *
from . import converters
from django.contrib.auth.decorators import login_required

register_converter(converters.MachineType, "machine_type")
register_converter(converters.MachineTypeSpecific, "machine")
register_converter(converters.MachineReservation, "reservation")
register_converter(converters.UserByUsername, "username")
register_converter(converters.Date, "%Y/%m/%d")
register_converter(converters.Year, "year")
register_converter(converters.Week, "week")
register_converter(converters.DateTime, "time")

json_urlpatterns = [
    path('<machine:machine>', get_future_reservations_machine, name="reservation_json"),
    path('<machine:machine>/<%Y/%m/%d:date>', get_reservations_day_and_machine, name="reservation_json"),
    path('<reservation:reservation>', get_future_reservations_machine_without_specific_reservation, name="reservation_json"),
]

quota_url_patterns = [
    path('update/3D-printer/', UpdateQuota3D.as_view()),
    path('update/sewing/', UpdateSewingQuota.as_view()),
    path('<username:user>/', get_user_quota_view),
    path('', QuotaView.as_view(), name="quota_panel"),
]


urlpatterns = [
    path('<year:year>/<week:week>/<machine:machine>', ReservationCalendarView.as_view(), name="reservation_calendar"),
    path('make/<machine:machine>/', login_required(MakeReservationView.as_view()), name="make_reservation"),
    path('make/<time:start_time>/<machine:machine>/', login_required(MakeReservationView.as_view()), name="make_reservation"),
    path('me/', login_required(MyReservationsView.as_view()), name="my_reservations"),
    path('delete/', login_required(DeleteReservationView.as_view()), name="delete_reservation"),
    path('change/<reservation:reservation>', login_required(ChangeReservationView.as_view()), name="change_reservation"),
    path('json/', include(json_urlpatterns)),
    path('quota/', include(quota_url_patterns)),
    re_path('^', MachineView.as_view(), name="reservation_machines_overview")
]
