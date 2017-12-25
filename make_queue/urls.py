from django.conf.urls import url
from make_queue.views import ReservationCalendarView, MakeReservationView, MyReservationsView, DeleteReservationView, ChangeReservationView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    url('^(?P<year>[0-9]{4})/(?P<week>([0-9]|[1-4][0-9]|5[0-3]))/(?P<machine_type>[a-zA-Z0-9-]+)?$', ReservationCalendarView.as_view(), name="reservation_calendar"),
    url('^make/((?P<start_time>([1-9]|1[0-2])/([1-9]|[12][0-9]|3[01])/([0-9]{4})/([01][0-9]|2[0-3]):([0-5][0-9]))/)?((?P<selected_machine_type>[a-zA-Z0-9-]+)/((?P<selected_machine_pk>[0-9]+)/)?)?$', login_required(MakeReservationView.as_view()), name="make_reservation"),
    url('^me/$', login_required(MyReservationsView.as_view()), name="my_reservations"),
    url('^delete/$', login_required(DeleteReservationView.as_view()), name="delete_reservation"),
    url('^change/(?P<machine_type>[a-zA-Z0-9-]+)/(?P<pk>([0-9]+))/', login_required(ChangeReservationView.as_view()), name="change_reservation"),
]
