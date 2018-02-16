from django.test import TestCase
from django.contrib.auth.models import User
from django.urls.base import reverse
from django.utils import timezone
import pytz
import mock
from make_queue.templatetags.reservation_extra import calendar_url_reservation, current_calendar_url
from make_queue.models import Printer3D, Quota3D, Reservation3D


class ReservationExtraTestCases(TestCase):

    def test_calendar_reservation_url(self):
        user = User.objects.create_user("user", "user@makentnu.no", "weak_pass")
        user.save()

        Quota3D.objects.create(user=user, max_time_reservation=10, max_number_of_reservations=2, can_print=True)
        printer = Printer3D.objects.create(name="U1", location="S1", model="Ultimaker", status="F")

        reservation = Reservation3D.objects.create(user=user, machine=printer, event=None,
                                                   start_time=pytz.timezone(
                                                       timezone.get_default_timezone_name()).localize(
                                                       timezone.datetime(2017, 12, 26, 17, 0)),
                                                   end_time=pytz.timezone(
                                                       timezone.get_default_timezone_name()).localize(
                                                       timezone.datetime(2017, 12, 26, 19, 0)))

        self.assertEqual(
            reverse('reservation_calendar',
                    kwargs={'year': 2017, 'week': 52, 'machine': printer}),
            calendar_url_reservation(reservation))

    @mock.patch('django.utils.timezone.now')
    def test_current_calendar_url(self, now_mock):
        date = timezone.datetime(2017, 12, 26, 12, 34, 0)
        now_mock.return_value = pytz.timezone(timezone.get_default_timezone_name()).localize(date)
        printer = Printer3D.objects.create(name="U1", location="S1", model="Ultimaker", status="F")

        self.assertEqual(reverse('reservation_calendar',
                                 kwargs={'year': 2017, 'week': 52, 'machine': printer}),
                         current_calendar_url(printer))
