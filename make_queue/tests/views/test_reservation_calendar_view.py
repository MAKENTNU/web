from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
import pytz
from make_queue.views import ReservationCalendarView
from make_queue.models import Printer3D, SewingMachine, Reservation3D, Quota3D


class ReservationCalendarViewTestCase(TestCase):

    def test_year_and_week_to_monday(self):
        date = datetime(2017, 12, 18)
        self.assertEqual(date, ReservationCalendarView.year_and_week_to_monday(2017, 51))

    def test_is_valid_week_with_zero_week_number(self):
        self.assertFalse(ReservationCalendarView.is_valid_week(2017, 0))

    def test_is_valid_week_with_valid_week(self):
        self.assertTrue(ReservationCalendarView.is_valid_week(2017, 51))

    def test_is_valid_week_with_to_high_week(self):
        self.assertFalse(ReservationCalendarView.is_valid_week(2017, 53))

    def test_get_next_valid_week_middle_of_year(self):
        self.assertEqual((2017, 30), ReservationCalendarView.get_next_valid_week(2017, 29, 1))
        self.assertEqual((2017, 28), ReservationCalendarView.get_next_valid_week(2017, 29, -1))

    def test_get_next_valid_week_year_shift(self):
        self.assertEqual((2018, 1), ReservationCalendarView.get_next_valid_week(2017, 52, 1))
        self.assertEqual((2016, 52), ReservationCalendarView.get_next_valid_week(2017, 1, -1))

    def test_get_machines_simple_printer(self):
        Printer3D.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(Printer3D.objects.all()), list(ReservationCalendarView.get_machines(Printer3D.literal)))

    def test_get_machines_simple_sewing_machine(self):
        SewingMachine.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(SewingMachine.objects.all()),
                         list(ReservationCalendarView.get_machines(SewingMachine.literal)))

    def test_get_machines_several(self):
        Printer3D.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        Printer3D.objects.create(name="S2", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(Printer3D.objects.all()), list(ReservationCalendarView.get_machines(Printer3D.literal)))

    def test_get_machines_several_types(self):
        SewingMachine.objects.create(name="K1", location="U1", model="Generic", status="F")
        Printer3D.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        Printer3D.objects.create(name="S2", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(Printer3D.objects.all()), list(ReservationCalendarView.get_machines(Printer3D.literal)))

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
        self.assertEqual(ReservationCalendarView.format_reservation(reservation, pytz.timezone(
            timezone.get_default_timezone_name()).localize(datetime(2017, 12, 25))), {
                             'reservation': reservation,
                             'start_percentage': 50,
                             'start_time': "11:00",
                             'end_time': "17:00",
                             'length': 25
                         })

    def test_format_reservation_start_day_before(self):
        reservation = self.create_reservation(datetime(2017, 12, 24, 12), datetime(2017, 12, 25, 6))
        self.assertEqual(ReservationCalendarView.format_reservation(reservation, pytz.timezone(
            timezone.get_default_timezone_name()).localize(datetime(2017, 12, 25))), {
                             'reservation': reservation,
                             'start_percentage': 0,
                             'start_time': "00:00",
                             'end_time': "05:00",
                             "length": 25
                         })

    def test_format_reservation_end_day_after(self):
        reservation = self.create_reservation(datetime(2017, 12, 25, 12), datetime(2017, 12, 26, 3))
        self.assertEqual(ReservationCalendarView.format_reservation(reservation, pytz.timezone(
            timezone.get_default_timezone_name()).localize(datetime(2017, 12, 25))), {
                             'reservation': reservation,
                             'start_percentage': 50,
                             'start_time': '11:00',
                             'end_time': "23:59",
                             'length': 50 - 100 / 1440
                         })
