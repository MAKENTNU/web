from datetime import timedelta
from unittest import mock

from django.templatetags.static import static
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from util.locale_utils import parse_datetime_localized
from ...models.course import Printer3DCourse
from ...models.machine import Machine, MachineType
from ...models.reservation import Quota, Reservation
from ...templatetags.reservation_extra import calendar_url_reservation, current_calendar_url, get_stream_image_path


class TestReservationExtra(TestCase):

    @mock.patch('django.utils.timezone.now')
    def test_calendar_reservation_url(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2018-12-09 12:24")
        user = User.objects.create_user("user", "user@makentnu.no", "weak_pass")

        printer_machine_type = MachineType.objects.get(pk=1)
        Quota.objects.create(user=user, number_of_reservations=2, ignore_rules=True,
                             machine_type=printer_machine_type)
        printer = Machine.objects.create(name="U1", location="S1", machine_model="Ultimaker", status=Machine.Status.AVAILABLE,
                                         machine_type=printer_machine_type)
        Printer3DCourse.objects.create(user=user, username=user.username, name=user.get_full_name(),
                                       date=timezone.now())

        reservation = Reservation.objects.create(user=user, machine=printer, event=None,
                                                 start_time=timezone.now(),
                                                 end_time=timezone.now() + timedelta(hours=2))

        self.assertEqual(calendar_url_reservation(reservation), current_calendar_url(printer))

    @mock.patch('django.utils.timezone.now')
    def test_current_calendar_url(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2017-12-26 12:34")
        printer_machine_type = MachineType.objects.get(pk=1)
        printer = Machine.objects.create(
            name="U1", location="S1", machine_model="Ultimaker", machine_type=printer_machine_type, status=Machine.Status.AVAILABLE,
        )

        self.assertEqual(
            current_calendar_url(printer),
            f"{reverse('machine_detail', args=[printer.pk])}?calendar_year=2017&calendar_week=52",
        )

        # Check the edge case of January 1st 2010 being week 53 of 2009
        now_mock.return_value = parse_datetime_localized("2010-01-01 12:34")
        self.assertEqual(
            current_calendar_url(printer),
            f"{reverse('machine_detail', args=[printer.pk])}?calendar_year=2009&calendar_week=53",
        )

    def test_get_stream_image_path_returns_correct_image_path(self):
        no_stream_image_path = static('make_queue/img/no_stream.svg')
        path_status_tuple_list = [
            (static('make_queue/img/maintenance.svg'), Machine.Status.MAINTENANCE),
            (static('make_queue/img/out_of_order.svg'), Machine.Status.OUT_OF_ORDER),
            (no_stream_image_path, Machine.Status.AVAILABLE),
            (no_stream_image_path, Machine.Status.IN_USE),
            (no_stream_image_path, Machine.Status.RESERVED),
        ]
        for static_path, machine_status in path_status_tuple_list:
            with self.subTest(static_path=static_path, machine_status=machine_status):
                result = get_stream_image_path(machine_status)
                self.assertEqual(result, static_path)
