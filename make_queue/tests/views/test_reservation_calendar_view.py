from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
import pytz
from make_queue.views.reservation.calendar import ReservationCalendarComponentView
from make_queue.models import Printer3D, Reservation3D, Quota3D


class ReservationCalendarComponentViewTestCase(TestCase):

    @staticmethod
    def create_reservation(start_time, end_time):
        Printer3D.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        user = User.objects.create_user("User", "user@makentnu.no", "unsecure_pass")
        user.save()
        Quota3D.objects.create(user=user, max_time_reservation=40, max_number_of_reservations=2, can_print=True)
        Reservation3D.objects.create(user=user, machine=Printer3D.objects.get(name="S1"),
                                     start_time=pytz.timezone(timezone.get_default_timezone_name()).localize(
                                         start_time),
                                     end_time=pytz.timezone(timezone.get_default_timezone_name()).localize(end_time),
                                     event=None)
        return Reservation3D.objects.first()

    def test_format_reservation_start_end_same_day(self):
        reservation = self.create_reservation(datetime(2017, 12, 25, 12), datetime(2017, 12, 25, 18))
        self.assertEqual(ReservationCalendarComponentView.format_reservation(reservation, pytz.timezone(
            timezone.get_default_timezone_name()).localize(datetime(2017, 12, 25))), {
                             'reservation': reservation,
                             'start_percentage': 50,
                             'start_time': "11:00",
                             'end_time': "17:00",
                             'length': 25
                         })

    def test_format_reservation_start_day_before(self):
        reservation = self.create_reservation(datetime(2017, 12, 24, 12), datetime(2017, 12, 25, 6))
        self.assertEqual(ReservationCalendarComponentView.format_reservation(reservation, pytz.timezone(
            timezone.get_default_timezone_name()).localize(datetime(2017, 12, 25))), {
                             'reservation': reservation,
                             'start_percentage': 0,
                             'start_time': "00:00",
                             'end_time': "05:00",
                             "length": 25
                         })

    def test_format_reservation_end_day_after(self):
        reservation = self.create_reservation(datetime(2017, 12, 25, 12), datetime(2017, 12, 26, 3))
        self.assertEqual(ReservationCalendarComponentView.format_reservation(reservation, pytz.timezone(
            timezone.get_default_timezone_name()).localize(datetime(2017, 12, 25))), {
                             'reservation': reservation,
                             'start_percentage': 50,
                             'start_time': '11:00',
                             'end_time': "23:59",
                             'length': 50 - 100 / 1440
                         })
