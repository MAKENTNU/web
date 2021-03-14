from datetime import timedelta
from unittest import mock

import pytz
from django.test import TestCase

from users.models import User
from make_queue.util.time import local_to_date
from ...models.course import Printer3DCourse
from ...models.models import Machine, MachineType, Quota, Reservation
from ...templatetags.reservation_extra import *


class ReservationExtraTestCases(TestCase):

    @mock.patch('django.utils.timezone.now')
    def test_calendar_reservation_url(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 12, 9, 12, 24))
        user = User.objects.create_user("user", "user@makentnu.no", "weak_pass")
        user.save()

        printer_machine_type = MachineType.objects.get(pk=1)
        Quota.objects.create(user=user, number_of_reservations=2, ignore_rules=True,
                             machine_type=printer_machine_type)
        printer = Machine.objects.create(name="U1", location="S1", machine_model="Ultimaker", status=Machine.AVAILABLE,
                                         machine_type=printer_machine_type)
        Printer3DCourse.objects.create(user=user, username=user.username, name=user.get_full_name(),
                                       date=timezone.now())

        reservation = Reservation.objects.create(user=user, machine=printer, event=None,
                                                 start_time=timezone.now(),
                                                 end_time=timezone.now() + timedelta(hours=2))

        self.assertEqual(current_calendar_url(printer), calendar_url_reservation(reservation))

    @mock.patch('django.utils.timezone.now')
    def test_current_calendar_url(self, now_mock):
        date = timezone.datetime(2017, 12, 26, 12, 34, 0)
        now_mock.return_value = timezone.get_default_timezone().localize(date)
        printer_machine_type = MachineType.objects.get(pk=1)
        printer = Machine.objects.create(
            name="U1", location="S1", machine_model="Ultimaker", machine_type=printer_machine_type, status=Machine.AVAILABLE,
        )

        self.assertEqual(
            reverse('reservation_calendar', kwargs={'year': 2017, 'week': 52, 'machine': printer}),
            current_calendar_url(printer)
        )

    @mock.patch('django.utils.timezone.now')
    def test_is_current_data(self, now_mock):
        date = timezone.datetime(2017, 3, 5, 11, 18, 0)
        now_mock.return_value = timezone.get_default_timezone().localize(date)

        self.assertTrue(is_current_date(timezone.now().date()))
        self.assertTrue(is_current_date((timezone.now() + timedelta(hours=1)).date()))
        self.assertFalse(is_current_date((timezone.now() + timedelta(days=1)).date()))
        self.assertFalse(is_current_date((timezone.now() + timedelta(days=-1)).date()))

    @mock.patch('django.utils.timezone.now')
    def test_get_current_time_of_day(self, now_mock):
        def set_mock_value(hours, minutes):
            date = timezone.datetime(2017, 3, 5, hours, minutes, 0)
            now_mock.return_value = timezone.get_default_timezone().localize(date)

        set_mock_value(12, 0)
        self.assertEqual(50, get_current_time_of_day())

        set_mock_value(0, 0)
        self.assertEqual(0, get_current_time_of_day())

        set_mock_value(13, 0)
        self.assertEqual((13 / 24) * 100, get_current_time_of_day())

    def test_date_to_percentage(self):
        date = timezone.datetime(2017, 3, 5, 12, 0, 0)
        self.assertEqual(50, date_to_percentage(date))

        date = timezone.datetime(2017, 3, 5, 0, 0, 0)
        self.assertEqual(0, date_to_percentage(date))

        date = timezone.datetime(2017, 3, 5, 17, 0, 0)
        self.assertEqual((17 / 24) * 100, date_to_percentage(date))

        date = timezone.datetime(2017, 3, 5, 17, 25, 0)
        self.assertEqual((17 / 24 + 25 / (24 * 60)) * 100, date_to_percentage(date))

    def test_invert(self):
        self.assertEqual("true", invert(0))
        self.assertEqual("false", invert(1))
        self.assertEqual("true", invert(""))
        self.assertEqual("false", invert("true"))
        self.assertEqual("false", invert("test"))
        self.assertEqual("true", invert(False))
        self.assertEqual("false", invert(True))
