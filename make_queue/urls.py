from django.conf.urls import url
from make_queue.views import ReservationCalendarView


urlpatterns = [
    url('^(?P<year>[0-9]{4})/(?P<week>([0-9]|[1-4][0-9]|5[0-2]))/(?P<machine_type>[a-zA-Z0-9-]+)$', ReservationCalendarView.as_view()),
]
