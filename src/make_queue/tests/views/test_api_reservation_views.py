from datetime import datetime, timedelta
from http import HTTPStatus
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.test import Client, TestCase
from django.utils.http import urlencode
from django_hosts import reverse

from news.models import Event, TimePlace
from users.models import User
from util.locale_utils import parse_datetime_localized
from ...api.views import APIReservationListView
from ...models.course import Printer3DCourse
from ...models.machine import Machine, MachineType
from ...models.reservation import Quota, Reservation


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
