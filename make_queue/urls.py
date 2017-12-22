from django.conf.urls import url
from make_queue.views import ReservationCalendarView, MakeReservationView


urlpatterns = [
    url('^(?P<year>[0-9]{4})/(?P<week>([0-9]|[1-4][0-9]|5[0-2]))/(?P<machine_type>[a-zA-Z0-9-]+)$', ReservationCalendarView.as_view()),
    url('^make/((?P<start_time>([1-9]|1[0-2])/([1-9]|[12][0-9]|3[01])/([0-9]{4})/([01][0-9]|2[0-3]):([0-5][0-9]))/)?((?P<selected_machine_type>[a-zA-Z0-9-]+)/((?P<selected_machine_pk>[0-9]+)/)?)?$', MakeReservationView.as_view()),
]
