from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone
import pytz

from make_queue.fields import MachineTypeField
from make_queue.models.course import Printer3DCourse
from make_queue.views.reservation.calendar import ReservationCalendarComponentView
from make_queue.models.models import Machine, Reservation, Quota


class ReservationCalendarComponentViewTestCase(TestCase):

    @staticmethod
    def create_reservation(start_time, end_time):
        machine_type = MachineTypeField.get_machine_type(1)
        Machine.objects.create(name="S1", location="U1", machine_model="Ultimaker", status="F",
                               machine_type=machine_type)
        user = User.objects.create_user("User", "user@makentnu.no", "unsecure_pass")
        user.save()
        Quota.objects.create(user=user, number_of_reservations=2, ignore_rules=True, machine_type=machine_type)
        Printer3DCourse.objects.create(user=user, username=user.username, name=user.get_full_name(),
                                       date=timezone.datetime.now().date())
        Reservation.objects.create(user=user, machine=Machine.objects.get(name="S1"),
                                   start_time=start_time,
                                   end_time=end_time,
                                   event=None)
        return Reservation.objects.first()

    def test_format_reservation_start_end_same_day(self):
        date = pytz.timezone(timezone.get_default_timezone_name()).localize(
            datetime.combine(timezone.now().date() + timedelta(days=1), datetime.min.time()))
        reservation = self.create_reservation(date + timedelta(hours=12), date + timedelta(hours=18))
        self.assertEqual(ReservationCalendarComponentView.format_reservation(reservation, date), {
            'reservation': reservation,
            'start_percentage': 50,
            'start_time': "11:00",
            'end_time': "17:00",
            'length': 25
        })

    def test_format_reservation_start_day_before(self):
        date = pytz.timezone(timezone.get_default_timezone_name()).localize(
            datetime.combine(timezone.now().date() + timedelta(days=1), datetime.min.time()))
        reservation = self.create_reservation(date + timedelta(hours=12), date + timedelta(days=1, hours=6))
        self.assertEqual(ReservationCalendarComponentView.format_reservation(reservation, date + timedelta(days=1)), {
            'reservation': reservation,
            'start_percentage': 0,
            'start_time': "00:00",
            'end_time': "05:00",
            "length": 25
        })

    def test_format_reservation_end_day_after(self):
        date = pytz.timezone(timezone.get_default_timezone_name()).localize(
            datetime.combine(timezone.now().date() + timedelta(days=1), datetime.min.time()))
        reservation = self.create_reservation(date + timedelta(hours=12), date + timedelta(days=1, hours=4))
        self.assertEqual(ReservationCalendarComponentView.format_reservation(reservation, date), {
            'reservation': reservation,
            'start_percentage': 50,
            'start_time': '11:00',
            'end_time': "23:59",
            'length': 50 - 100 / 1440
        })
