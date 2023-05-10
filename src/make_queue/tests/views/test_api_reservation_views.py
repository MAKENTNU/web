from datetime import datetime, timedelta
from http import HTTPStatus
from unittest import mock
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import Client, TestCase
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.utils.http import urlencode
from django_hosts import reverse

from news.models import Event, TimePlace
from users.models import User
from util.locale_utils import parse_datetime_localized
from ...api.views import APIReservationListView
from ...models.course import Printer3DCourse
from ...models.machine import Machine, MachineType
from ...models.reservation import Quota, Reservation, ReservationRule
from ...templatetags.reservation_extra import can_change_reservation


Day = ReservationRule.Day


class APIReservationListViewTests(TestCase):

    def setUp(self):
        now = parse_datetime_localized("2020-01-01 00:00")

        self.admin = User.objects.create_user("admin")
        self.admin.add_perms('make_queue.can_create_event_reservation', 'make_queue.can_view_reservation_user')
        self.user = User.objects.create_user("user")

        self.admin_client = Client()
        self.user_client = Client()
        self.admin_client.force_login(self.admin)
        self.user_client.force_login(self.user)

        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        printer_machine_type = MachineType.objects.get(pk=1)
        self.machine1 = Machine.objects.create(name="Machine 1", machine_type=printer_machine_type)

        Printer3DCourse.objects.create(user=self.admin, username=self.admin.username, date=now)
        Printer3DCourse.objects.create(user=self.user, username=self.user.username, date=now)
        Quota.objects.create(all=True, machine_type=printer_machine_type, number_of_reservations=10, ignore_rules=True)

        event = Event.objects.create(title="Test event")
        time_place = TimePlace.objects.create(event=event, start_time=now, end_time=now + timedelta(hours=2))

        # Have to do this when validation is done in `Reservation.save()`,
        # to not make it raise an error when creating reservations in the past
        with mock.patch('django.utils.timezone.now') as now_mock:
            now_mock.return_value = now

            self.reservation1 = Reservation.objects.create(
                machine=self.machine1, user=self.admin,
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=2),
                special=True, special_text="Test",
            )
            self.reservation2 = Reservation.objects.create(
                machine=self.machine1, user=self.admin,
                start_time=now + timedelta(hours=2),
                end_time=now + timedelta(hours=3),
            )
            self.reservation3 = Reservation.objects.create(
                machine=self.machine1, user=self.admin,
                start_time=now + timedelta(hours=3),
                end_time=now + timedelta(hours=4),
                event=time_place,
            )
            self.reservation4 = Reservation.objects.create(
                machine=self.machine1, user=self.user,
                start_time=now + timedelta(hours=4),
                end_time=now + timedelta(hours=5),
            )

        self.machine1_url = reverse('api_reservation_list', args=[self.machine1.pk])

    def test_responds_with_expected_json_for_various_datetimes(self):
        # Facilitates printing the whole diff if the tests fail, which is useful due to the long dict strings in this test case
        self.maxDiff = None

        def assert_user_info_in_json(json_dict: dict, boolean: bool):
            assert_in_or_not_in = self.assertIn if boolean else self.assertNotIn
            assert_in_or_not_in('user', json_dict)
            assert_in_or_not_in('email', json_dict)

        def assert_response_contains(*, start: datetime | str, end: datetime | str, expected_reservations: list[Reservation]):
            for user, client in ((self.admin, self.admin_client),
                                 (self.user, self.user_client),
                                 (AnonymousUser(), Client())):
                with self.subTest(user=user):
                    response = client.get(f"{self.machine1_url}?{urlencode({'start_date': start, 'end_date': end})}")
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    response_json = response.json()
                    self.assertDictEqual(response_json, {'reservations': [
                        APIReservationListView.build_reservation_dict(reservation, user)
                        for reservation in expected_reservations
                    ]})
                    for reservation, reservation_json in zip(expected_reservations, response_json['reservations'], strict=True):
                        # The response should only contain the user info if an admin is viewing the page, and if it's a reservation "owned" by MAKE
                        user_info_present = user == self.admin and not reservation.special and not reservation.event
                        assert_user_info_in_json(reservation_json, user_info_present)

        assert_response_contains(start="2020-01-01", end="2020-01-31", expected_reservations=[
            self.reservation1, self.reservation2, self.reservation3, self.reservation4])
        assert_response_contains(start="2020-01-01 01:00", end="2020-01-01 02:00", expected_reservations=[
            self.reservation1])
        # Seconds should be accepted
        assert_response_contains(start="2020-01-01 01:10:10", end="2020-01-01 01:50:50", expected_reservations=[
            self.reservation1])
        # Time zones should be accepted
        assert_response_contains(start="2020-01-01T04:00+01:00", end="2020-01-01T03:00-01:00", expected_reservations=[
            self.reservation4])

        # The inclusion precision of reservations should be on a level of seconds
        one_sec = timedelta(seconds=1)
        assert_response_contains(start=self.reservation1.end_time, end=self.reservation4.start_time, expected_reservations=[
            self.reservation2, self.reservation3])
        assert_response_contains(start=self.reservation1.end_time - one_sec, end=self.reservation4.start_time + one_sec, expected_reservations=[
            self.reservation1, self.reservation2, self.reservation3, self.reservation4])

        # If start and end are equal, no reservations should be returned, since the time interval is 0
        assert_response_contains(start=self.reservation2.start_time, end=self.reservation2.start_time, expected_reservations=[])
        assert_response_contains(start=self.reservation2.start_time, end=self.reservation2.start_time + one_sec, expected_reservations=[
            self.reservation2])

    def test_responds_with_expected_query_parameter_errors(self):
        def assert_error_response_contains(query: str, *, expected_json_dict: dict):
            for user, client in ((self.admin, self.admin_client),
                                 (self.user, self.user_client),
                                 (AnonymousUser(), Client())):
                with self.subTest(user=user):
                    response = client.get(f"{self.machine1_url}?{query}" if query else self.machine1_url)
                    self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
                    self.assertDictEqual(response.json(), expected_json_dict)

        field_required = "Feltet er påkrevet."
        value_not_datetime = "Oppgi gyldig dato og tidspunkt."
        undefined_asdf_field = {'undefined_fields': {'message': "These provided fields are not defined in the API.", 'fields': ['asdf']}}

        assert_error_response_contains("", expected_json_dict={
            'field_errors': {'start_date': [field_required], 'end_date': [field_required]}})
        assert_error_response_contains("start_date=2020-01-01", expected_json_dict={
            'field_errors': {'end_date': [field_required]}})
        assert_error_response_contains("end_date=2020-01-31", expected_json_dict={
            'field_errors': {'start_date': [field_required]}})
        assert_error_response_contains("start_date=2020-01-01&end_date=2020-02", expected_json_dict={
            'field_errors': {'end_date': [value_not_datetime]}})
        assert_error_response_contains("start_date=2020-01&end_date=2020-02-01", expected_json_dict={
            'field_errors': {'start_date': [value_not_datetime]}})
        assert_error_response_contains("start_date=asdf&end_date=asdf", expected_json_dict={
            'field_errors': {'start_date': [value_not_datetime], 'end_date': [value_not_datetime]}})

        assert_error_response_contains("start_date=2020-01-01 01:50&end_date=2020-01-01 01:10", expected_json_dict={
            'field_errors': {'start_date': ["This must be before 'end_date'."], 'end_date': ["This must be after 'start_date'."]}})

        assert_error_response_contains("start_date=2020-01-01&end_date=2020-01-31&asdf=asdf", expected_json_dict={
            **undefined_asdf_field})
        assert_error_response_contains("start_date=2020-01-01&asdf=asdf", expected_json_dict={
            'field_errors': {'end_date': [field_required]}, **undefined_asdf_field})
        assert_error_response_contains("end_date=2020-01&asdf=asdf", expected_json_dict={
            'field_errors': {'start_date': [field_required], 'end_date': [value_not_datetime]}, **undefined_asdf_field})


class TestAPIReservationMarkFinishedView(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("test")
        self.client.force_login(self.user)
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.machine_type = MachineType.objects.get(pk=2)
        self.machine = Machine.objects.create(machine_type=self.machine_type, status=Machine.Status.AVAILABLE, name="Test")
        Quota.objects.create(machine_type=self.machine_type, number_of_reservations=2, ignore_rules=False, all=True)
        ReservationRule.objects.create(
            machine_type=self.machine_type, start_time=parse_time("00:00"), days_changed=6, end_time=parse_time("23:59"),
            start_days=[Day.MONDAY], max_hours=6, max_inside_border_crossed=6,
        )
        self.now = timezone.localtime()
        self.reservation1 = Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=2),
        )

    def post_to(self, reservation: Reservation):
        return self.client.post(reverse('api_reservation_mark_finished', args=[reservation.pk]))

    def test_get_request_fails(self):
        response = self.client.get(reverse('api_reservation_mark_finished', args=[self.reservation1.pk]))
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    @patch('django.utils.timezone.now')
    def test_valid_post_request_succeeds(self, now_mock):
        # Freeze the return value of `timezone.now()` and set it to 1 minute after `self.reservation1` has started
        now_mock.return_value = self.now + timedelta(hours=1, minutes=1)
        self.assertTrue(can_change_reservation(self.reservation1, self.user))

        response = self.post_to(self.reservation1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.reservation1.refresh_from_db()
        self.assertEqual(self.reservation1.end_time, timezone.now())

    def test_finishing_before_start_fails(self):
        original_end_time = self.reservation1.end_time
        response = self.post_to(self.reservation1)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.reservation1.refresh_from_db()
        self.assertEqual(self.reservation1.end_time, original_end_time,
                         "Marking a reservation in the future as finished should not be possible")

    @patch('django.utils.timezone.now')
    def test_finishing_after_end_fails(self, now_mock):
        # Set "now" to 1 hour after `self.reservation1` has ended
        now_mock.return_value = self.now + timedelta(hours=3)

        original_end_time = self.reservation1.end_time
        response = self.post_to(self.reservation1)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.reservation1.refresh_from_db()
        self.assertEqual(self.reservation1.end_time, original_end_time,
                         "Marking a reservation in the past as finished should not do anything")

    @patch('django.utils.timezone.now')
    def test_finishing_just_before_other_reservation_starts_succeeds(self, now_mock):
        # Freeze the return value of `timezone.now()`
        now_mock.return_value = self.now

        self.reservation1.delete()
        reservation2 = Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=self.now + timedelta(minutes=1),
            end_time=self.now + timedelta(hours=6),
        )
        reservation3 = Reservation.objects.create(
            machine=self.machine, user=User.objects.create_user("test2"),
            start_time=self.now + timedelta(hours=6),
            end_time=self.now + timedelta(hours=6, minutes=26),
        )

        # Set "now" to 3 minutes before `reservation2` ends and `reservation3` starts
        now_mock.return_value = self.now + timedelta(hours=5, minutes=57)
        response = self.post_to(reservation2)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        reservation2.refresh_from_db()
        self.assertEqual(reservation2.end_time, timezone.now())

    @patch('django.utils.timezone.now')
    def test_can_finish_existing_reservations_for_machine_out_of_order_or_on_maintenance(self, now_mock):
        # Freeze the return value of `timezone.now()`
        now_mock.return_value = self.now

        for machine_status in (Machine.Status.OUT_OF_ORDER, Machine.Status.MAINTENANCE):
            with self.subTest(machine_status=machine_status):
                machine = self.reservation1.machine
                machine.status = machine_status
                machine.save()

                # Set "now" to 5 minutes before `self.reservation1` ends
                now_mock.return_value = self.reservation1.end_time - timedelta(minutes=5)

                response = self.post_to(self.reservation1)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.reservation1.refresh_from_db()
                self.assertEqual(self.reservation1.end_time, timezone.now())


class TestAPIReservationDeleteView(TestCase):

    def setUp(self):
        password = "weak_pass"
        self.user1 = User.objects.create_user("user1", "user1@makentnu.no", password)
        self.user2 = User.objects.create_user("user2", "user2@makentnu.no", password)
        self.client1 = Client()
        self.client2 = Client()
        self.client1.login(username=self.user1.username, password=password)
        self.client2.login(username=self.user2.username, password=password)

        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        printer_machine_type = MachineType.objects.get(pk=1)
        self.machine1 = Machine.objects.create(
            name="U1", machine_model="Ultimaker 2", machine_type=printer_machine_type,
            location="MAKE", status=Machine.Status.AVAILABLE,
        )

        Quota.objects.create(user=self.user1, number_of_reservations=2, ignore_rules=True, machine_type=printer_machine_type)
        Quota.objects.create(user=self.user2, number_of_reservations=2, ignore_rules=True, machine_type=printer_machine_type)

        now = timezone.localtime()
        Printer3DCourse.objects.create(user=self.user1, username=self.user1.username, name=self.user1.get_full_name(), date=now)
        Printer3DCourse.objects.create(user=self.user2, username=self.user2.username, name=self.user2.get_full_name(), date=now)

        self.reservation = Reservation.objects.create(
            user=self.user1,
            machine=self.machine1,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=4),
        )

    def test_delete_own_reservation_succeeds(self):
        response = self.client1.delete(reverse('api_reservation_delete', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_other_users_reservation_fails(self):
        response = self.client2.delete(reverse('api_reservation_delete', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_only_one_among_multiple_reservations_succeeds(self):
        now = timezone.localtime()
        reservation2 = Reservation.objects.create(
            user=self.user1,
            machine=self.machine1,
            start_time=now + timedelta(hours=6),
            end_time=now + timedelta(hours=8),
        )

        response = self.client1.delete(reverse('api_reservation_delete', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())
        self.assertTrue(Reservation.objects.filter(pk=reservation2.pk).exists())

    def test_delete_reservation_after_start_fails(self):
        now = timezone.localtime()
        Reservation.objects.filter(pk=self.reservation.pk).update(start_time=now)
        response = self.client1.delete(reverse('api_reservation_delete', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertTrue(Reservation.objects.filter(pk=self.reservation.pk).exists())

        # Setting the start time to the future should allow deletion
        Reservation.objects.filter(pk=self.reservation.pk).update(start_time=now + timedelta(hours=1))
        response = self.client1.delete(reverse('api_reservation_delete', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_can_cancel_existing_reservation_for_machine_out_of_order(self):
        self._test_can_cancel_existing_reservation_for_machine_with_status(Machine.Status.OUT_OF_ORDER)

    def test_can_cancel_existing_reservation_for_machine_on_maintenance(self):
        self._test_can_cancel_existing_reservation_for_machine_with_status(Machine.Status.MAINTENANCE)

    def _test_can_cancel_existing_reservation_for_machine_with_status(self, machine_status: Machine.Status):
        machine = self.reservation.machine
        machine.status = machine_status
        machine.save()

        response = self.client1.delete(reverse('api_reservation_delete', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())
