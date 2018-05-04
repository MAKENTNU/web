from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
import pytz
import mock
from make_queue.templatetags.reservation_extra import *
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

    @mock.patch('django.utils.timezone.now')
    def test_is_current_data(self, now_mock):
        date = timezone.datetime(2017, 3, 5, 11, 18, 0)
        now_mock.return_value = pytz.timezone(timezone.get_default_timezone_name()).localize(date)

        self.assertTrue(is_current_date(timezone.now().date()))
        self.assertTrue(is_current_date((timezone.now() + timedelta(hours=1)).date()))
        self.assertFalse(is_current_date((timezone.now() + timedelta(days=1)).date()))
        self.assertFalse(is_current_date((timezone.now() + timedelta(days=-1)).date()))

    @mock.patch('django.utils.timezone.now')
    def test_get_current_time_of_day(self, now_mock):
        def set_mock_value(hours, minutes):
            date = timezone.datetime(2017, 3, 5, hours, minutes, 0)
            now_mock.return_value = pytz.timezone(timezone.get_default_timezone_name()).localize(date)

        set_mock_value(12, 0)
        self.assertEqual(50, get_current_time_of_day())

        set_mock_value(0, 0)
        self.assertEqual(0, get_current_time_of_day())

        set_mock_value(13, 0)
        self.assertEqual((13/24)*100, get_current_time_of_day())

    def test_date_to_percentage(self):
        date = timezone.datetime(2017, 3, 5, 12, 0, 0)
        self.assertEqual(50, date_to_percentage(date))

        date = timezone.datetime(2017, 3, 5, 0, 0, 0)
        self.assertEqual(0, date_to_percentage(date))

        date = timezone.datetime(2017, 3, 5, 17, 0, 0)
        self.assertEqual((17/24)*100, date_to_percentage(date))

        date = timezone.datetime(2017, 3, 5, 17, 25, 0)
        self.assertEqual((17/24 + 25/1440)*100, date_to_percentage(date))

    def test_invert(self):
        self.assertEqual("true", invert(0))
        self.assertEqual("false", invert(1))
        self.assertEqual("true", invert(""))
        self.assertEqual("false", invert("true"))
        self.assertEqual("false", invert("test"))
        self.assertEqual("true", invert(False))
        self.assertEqual("false", invert(True))
