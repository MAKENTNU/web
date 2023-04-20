from abc import ABC
from collections.abc import Callable
from datetime import timedelta
from http import HTTPStatus
from typing import Type
from unittest.mock import patch

from django.http import HttpResponse
from django.test import Client, TestCase
from django.utils import timezone
from django.utils.dateparse import parse_time
from django_hosts import reverse

from news.models import Event, TimePlace
from users.models import User
from util.locale_utils import iso_datetime_format, parse_datetime_localized
from util.test_utils import set_without_duplicates
from ..utility import post_request_with_user, request_with_user
from ...forms.reservation import ReservationForm, ReservationListQueryForm
from ...models.course import Printer3DCourse
from ...models.machine import Machine, MachineType
from ...models.reservation import Quota, Reservation, ReservationRule
from ...templatetags.reservation_extra import can_change_reservation
from ...views.reservation import ReservationCreateView, ReservationUpdateView


Day = ReservationRule.Day


class ReservationCreateOrUpdateViewTestBase(TestCase, ABC):

    def setUp(self):
        Reservation.FUTURE_LIMIT = timedelta(days=7)
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.sewing_machine_type = MachineType.objects.get(pk=2)
        self.user = User.objects.create_user(username="test")
        self.machine = Machine.objects.create(machine_model="Test", machine_type=self.sewing_machine_type)
        self.event = Event.objects.create(title="Test_event")
        Quota.objects.create(user=self.user, machine_type=self.sewing_machine_type, number_of_reservations=100,
                             ignore_rules=True)
        self.timeplace = TimePlace.objects.create(event=self.event,
                                                  start_time=timezone.localtime() + timedelta(hours=1),
                                                  end_time=timezone.localtime() + timedelta(hours=2))

    def get_view(self, view_class: Type[ReservationCreateView] | Type[ReservationUpdateView], **kwargs):
        view = view_class()
        view.setup(request_with_user(self.user), **kwargs)
        return view

    def create_form(self, *, start_time_delta: timedelta, end_time_delta: timedelta, event=None, special=False, special_text=""):
        return ReservationForm(data=self.create_form_data(start_time_delta, end_time_delta, event, special, special_text))

    def create_form_data(self, start_time_delta: timedelta, end_time_delta: timedelta, event=None, special=False, special_text=""):
        now = timezone.now()
        return {
            'start_time': iso_datetime_format(now + start_time_delta),
            'end_time': iso_datetime_format(now + end_time_delta),
            'event': event is not None, 'event_pk': 0 if event is None else event.pk, 'special': special,
            'special_text': special_text, 'machine_name': self.machine.pk,
        }


class TestReservationCreateOrUpdateView(ReservationCreateOrUpdateViewTestBase):

    def test_get_error_message_non_event(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2))
        self.assertTrue(form.is_valid())
        reservation = Reservation(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        view = self.get_view(ReservationCreateView, pk=self.machine.pk)
        self.assertEqual(view.get_error_message(form, reservation),
                         "Det er ikke mulig å reservere maskinen på dette tidspunktet. Sjekk reglene for hvilke "
                         "perioder det er mulig å reservere maskinen i")

    def test_get_error_message_event(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2), event=self.event)
        self.assertTrue(form.is_valid())
        reservation = Reservation(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        self.user.add_perms('make_queue.can_create_event_reservation')
        view = self.get_view(ReservationCreateView, pk=self.machine.pk)
        self.assertEqual(view.get_error_message(form, reservation),
                         "Tidspunktet eller arrangementet er ikke lenger tilgjengelig")

    def test_get_error_message_too_far_in_the_future(self):
        form = self.create_form(start_time_delta=Reservation.FUTURE_LIMIT,
                                end_time_delta=Reservation.FUTURE_LIMIT + timedelta(hours=1))
        self.assertTrue(form.is_valid())
        reservation = Reservation(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        view = self.get_view(ReservationCreateView, pk=self.machine.pk)
        self.assertEqual(view.get_error_message(form, reservation),
                         f"Reservasjoner kan bare lages {Reservation.FUTURE_LIMIT.days} dager fram i tid")

    def test_get_error_message_machine_out_of_order(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2))
        self.assertTrue(form.is_valid())
        machine = Machine.objects.create(machine_model="Test", machine_type=self.sewing_machine_type,
                                         status=Machine.Status.OUT_OF_ORDER, name="test out of order")
        reservation = Reservation(
            machine=machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        view = self.get_view(ReservationCreateView, pk=machine.pk)
        self.assertEqual(view.get_error_message(form, reservation),
                         "Maskinen er i ustand")

    def test_validate_and_save_valid_reservation(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2))
        self.assertTrue(form.is_valid())
        reservation = Reservation(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        view = self.get_view(ReservationCreateView, pk=self.machine.pk)
        response = view.validate_and_save(reservation, form)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_validate_and_save_non_valid_reservation(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2))
        self.assertTrue(form.is_valid())
        # Test with collision
        Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        reservation = Reservation(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        view = self.get_view(ReservationCreateView, pk=self.machine.pk)
        response = view.validate_and_save(reservation, form)
        # Second reservation should not be saved
        self.assertEqual(Reservation.objects.count(), 1)
        # 200 to re-render the form
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_context_data_reservation(self):
        self.user.add_perms('make_queue.can_create_event_reservation')
        now = timezone.localtime()
        reservation = Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            event=self.timeplace, comment="Comment",
        )
        view = self.get_view(ReservationUpdateView, pk=reservation.pk)
        context_data = view.get_context_data(pk=reservation.pk)
        context_data["machine_types"] = set(context_data["machine_types"])

        self.assertDictEqual(context_data, {
            "can_change_start_time": True,
            "can_change_end_time": True,
            "event_timeplaces": [self.timeplace],
            "new_reservation": False,
            "machine_types": {
                machine_type for machine_type in MachineType.objects.all()
                if machine_type.can_user_use(self.user)
            },
            "start_time": reservation.start_time,
            "end_time": reservation.end_time,
            "selected_machine": self.machine,
            "event": self.timeplace,
            "special": False,
            "special_text": "",
            "maximum_days_in_advance": Reservation.FUTURE_LIMIT.days,
            "comment": "Comment",
            "reservation": reservation,
        })

    def test_get_context_data_non_reservation(self):
        start_time = timezone.localtime() + timedelta(hours=1)
        view = self.get_view(ReservationCreateView, pk=self.machine.pk)
        context_data = view.get_context_data(machine_pk=self.machine.pk, start_time=start_time)
        context_data["machine_types"] = set(context_data["machine_types"])

        self.assertDictEqual(context_data, {
            "can_change_start_time": True,
            "can_change_end_time": True,
            "event_timeplaces": [self.timeplace],
            "new_reservation": True,
            "machine_types": {
                machine_type for machine_type in MachineType.objects.all()
                if machine_type.can_user_use(self.user)
            },
            "start_time": start_time,
            "selected_machine": self.machine,
            "maximum_days_in_advance": Reservation.FUTURE_LIMIT.days,
        })

    def test_post_valid_form(self):
        view = self.get_view(ReservationCreateView, pk=self.machine.pk)
        view.request = post_request_with_user(self.user, data=self.create_form_data(timedelta(hours=1), timedelta(hours=2)))
        # Need to handle the valid form function
        valid_form_calls = {"calls": 0}
        view.form_valid = lambda _form, **_kwargs: (
                valid_form_calls.update({"calls": valid_form_calls["calls"] + 1})
                or HttpResponse()
        )

        self.assertTrue(ReservationForm(view.request.POST).is_valid())
        response = view.handle_post(view.request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(valid_form_calls["calls"], 1)


class TestReservationCreateView(ReservationCreateOrUpdateViewTestBase):

    def get_view(self, view_class=ReservationCreateView, **kwargs):
        return super().get_view(view_class, **{
            'pk': self.machine.pk,
            **kwargs,
        })

    def test_only_users_with_3d_printer_course_can_view_create_reservation_page_for_3d_printers(self):
        printer_machine_type = MachineType.objects.get(pk=1)
        machine = Machine.objects.create(name="Lovelace", machine_model="Ultimaker 2+", machine_type=printer_machine_type)
        reservation_create_url = reverse('reservation_create', args=[machine.pk])

        self.client.force_login(self.user)
        # Not having taken the course should deny the user
        response = self.client.get(reservation_create_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        Printer3DCourse.objects.create(user=self.user, date=timezone.now())
        # Having taken the course should allow the user
        response = self.client.get(reservation_create_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self._test_only_internal_users_can_view_create_reservation_page_for_machine(self.user, machine)

    def test_only_users_with_raise3d_course_can_view_create_reservation_page_for_raise3d_printers(self):
        def set_raise3d_course(course: Printer3DCourse):
            course.raise3d_course = True
            course.save()

        raise3d_machine_type = MachineType.objects.get(pk=6)
        machine = Machine.objects.create(name="Darwin", machine_model="Raise3D Pro2 Plus", machine_type=raise3d_machine_type)
        self._test_only_users_with_advanced_course_can_view_create_reservation_page_for_advanced_printers(machine, set_raise3d_course)

    def test_only_users_with_sla_course_can_view_create_reservation_page_for_sla_printers(self):
        def set_sla_course(course: Printer3DCourse):
            course.sla_course = True
            course.save()

        sla_machine_type = MachineType.objects.get(pk=7)
        machine = Machine.objects.create(name="Unnamed SLA printer", machine_model="Formlabs Form 2", machine_type=sla_machine_type)
        self._test_only_users_with_advanced_course_can_view_create_reservation_page_for_advanced_printers(machine, set_sla_course)

    def _test_only_users_with_advanced_course_can_view_create_reservation_page_for_advanced_printers(
            self, machine: Machine, set_advanced_course_func: Callable[[Printer3DCourse], None],
    ):
        reservation_create_url = reverse('reservation_create', args=[machine.pk])

        self.client.force_login(self.user)
        # Not having taken the course at all should deny the user
        response = self.client.get(reservation_create_url)
        # `NOT_FOUND` for SLA printers, `FORBIDDEN` otherwise
        self.assertIn(response.status_code, {HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND})

        course = Printer3DCourse.objects.create(user=self.user, date=timezone.now())
        # Not having taken the advanced course should deny the user
        response = self.client.get(reservation_create_url)
        # `NOT_FOUND` for SLA printers, `FORBIDDEN` otherwise
        self.assertIn(response.status_code, {HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND})

        # Having taken the advanced course should allow the user
        set_advanced_course_func(course)
        response = self.client.get(reservation_create_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self._test_only_internal_users_can_view_create_reservation_page_for_machine(self.user, machine)

    def _test_only_internal_users_can_view_create_reservation_page_for_machine(self, user: User, machine: Machine):
        reservation_create_url = reverse('reservation_create', args=[machine.pk])
        self.client.force_login(user)

        # User should be allowed when machine is not internal
        response = self.client.get(reservation_create_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # User should not be able to find the machine when it's internal
        machine.internal = True
        machine.save()
        response = self.client.get(reservation_create_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # User should be allowed when they're internal
        user.add_perms('internal.is_internal')
        response = self.client.get(reservation_create_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_form_valid_normal_reservation(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2))
        self.assertTrue(form.is_valid())
        view = self.get_view()
        view.form_valid(form)
        self.assertEqual(Machine.objects.count(), 1)

    def test_form_valid_event_reservation(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2), event=self.timeplace)
        self.assertTrue(form.is_valid())
        self.user.add_perms('make_queue.can_create_event_reservation')
        view = self.get_view()
        view.form_valid(form)
        self.assertEqual(Machine.objects.count(), 1)

    def test_form_valid_special_reservation(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2), special=True, special_text="Test special")
        self.assertTrue(form.is_valid())
        self.user.add_perms('make_queue.can_create_event_reservation')
        view = self.get_view()
        view.form_valid(form)
        self.assertEqual(Machine.objects.count(), 1)

    def test_form_valid_invalid_reservation(self):
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2))
        self.assertTrue(form.is_valid())
        Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )
        view = self.get_view()
        response = view.form_valid(form)
        # Second reservation should not have been saved
        self.assertEqual(Machine.objects.count(), 1)
        # Re-rendering of form
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestReservationUpdateView(ReservationCreateOrUpdateViewTestBase):

    def get_view(self, view_class=ReservationUpdateView, **kwargs):
        return super().get_view(view_class, **kwargs)

    def create_reservation(self, form):
        self.assertTrue(form.is_valid())
        return Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
        )

    def test_post_changeable_reservation(self):
        reservation = self.create_reservation(self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2)))
        view = self.get_view(pk=reservation.pk)
        view.request.method = 'POST'
        response = view.dispatch(view.request, pk=reservation.pk)
        # Response should be the edit page for the reservation, as no form is posted with the data
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertListEqual(response.template_name, ['make_queue/reservation_form.html'])

    @patch("django.utils.timezone.now")
    def test_post_unchangeable_reservation(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2018-08-12 12:00")

        reservation = self.create_reservation(self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2)))

        now_mock.return_value = timezone.localtime() + timedelta(hours=2, minutes=1)

        view = self.get_view(pk=reservation.pk)
        view.request.method = 'POST'
        response = view.dispatch(view.request, pk=reservation.pk)
        # An unchangeable reservation should have redirect
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    @patch("django.utils.timezone.now")
    def test_form_valid_normal_reservation(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2018-08-12 12:00")

        reservation = self.create_reservation(self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2)))
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=3))
        self.assertTrue(form.is_valid())
        view = self.get_view(pk=reservation.pk)
        response = view.form_valid(form)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Reservation.objects.first().end_time, timezone.localtime() + timedelta(hours=3))

    @patch("django.utils.timezone.now")
    def test_form_valid_changed_machine(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2018-08-12 12:00")

        reservation = self.create_reservation(self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2)))
        old_machine = self.machine
        self.machine = Machine.objects.create(name="M1", machine_model="Generic", machine_type=self.sewing_machine_type)
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=3))
        self.assertTrue(form.is_valid())
        view = self.get_view(pk=reservation.pk)
        response = view.form_valid(form)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Reservation.objects.first().end_time, timezone.localtime() + timedelta(hours=2))
        self.assertEqual(Reservation.objects.first().machine, old_machine)

    @patch("django.utils.timezone.now")
    def test_form_valid_event_reservation(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2018-08-12 12:00")

        self.user.add_perms('make_queue.can_create_event_reservation')
        now = timezone.localtime()
        reservation = Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            event=self.timeplace,
        )
        self.timeplace = TimePlace.objects.create(event=self.event,
                                                  start_time=now + timedelta(hours=1),
                                                  end_time=now + timedelta(hours=2))
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2), event=self.timeplace)
        self.assertTrue(form.is_valid())
        view = self.get_view(pk=reservation.pk)
        response = view.form_valid(form)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Reservation.objects.first().event, self.timeplace)

    @patch("django.utils.timezone.now")
    def test_form_valid_special_reservation(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2018-08-12 12:00")

        self.user.add_perms('make_queue.can_create_event_reservation')
        now = timezone.localtime()
        reservation = Reservation.objects.create(
            machine=self.machine, user=self.user,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            special=True, special_text="Test",
        )
        form = self.create_form(start_time_delta=timedelta(hours=1), end_time_delta=timedelta(hours=2), special=True, special_text="Test2")
        self.assertTrue(form.is_valid())
        view = self.get_view(pk=reservation.pk)
        response = view.form_valid(form)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Reservation.objects.first().special_text, "Test2")


class TestReservationListView(TestCase):

    def setUp(self):
        now = timezone.localtime()
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        printer_machine_type = MachineType.objects.get(pk=1)
        sewing_machine_type = MachineType.objects.get(pk=2)

        self.admin = User.objects.create_user("admin")
        self.admin.add_perms('make_queue.can_create_event_reservation')
        self.user = User.objects.create_user("user")

        self.admin_client = Client()
        self.user_client = Client()
        self.admin_client.force_login(self.admin)
        self.user_client.force_login(self.user)

        Printer3DCourse.objects.create(user=self.admin, username=self.admin.username, date=now)
        Printer3DCourse.objects.create(user=self.user, username=self.user.username, date=now)
        Quota.objects.create(all=True, machine_type=printer_machine_type, number_of_reservations=10, ignore_rules=True)
        Quota.objects.create(all=True, machine_type=sewing_machine_type, number_of_reservations=10, ignore_rules=True)

        event = Event.objects.create(title="Test_event")
        time_place = TimePlace.objects.create(event=event, start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2))

        printer = Machine.objects.create(name="Blobbin'", machine_model="Ultimaker", machine_type=printer_machine_type)
        self.special_reservation_by_admin = Reservation.objects.create(
            machine=printer, user=self.admin,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            special=True, special_text="Test",
        )
        self.normal_reservation_by_admin = Reservation.objects.create(
            machine=printer, user=self.admin,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )
        self.event_reservation_by_admin = Reservation.objects.create(
            machine=printer, user=self.admin,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
            event=time_place,
        )
        self.normal_reservation_by_user = Reservation.objects.create(
            machine=printer, user=self.user,
            start_time=now + timedelta(hours=4),
            end_time=now + timedelta(hours=5),
        )

        sewing_machine = Machine.objects.create(name="Bobbin hehe", machine_model="Janome", machine_type=sewing_machine_type)
        self.sewing_reservation_by_admin = Reservation.objects.create(
            machine=sewing_machine, user=self.admin,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        self.sewing_reservation_by_user = Reservation.objects.create(
            machine=sewing_machine, user=self.user,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )

        self.Owner = ReservationListQueryForm.Owner
        self.base_url = reverse('reservation_list')
        self.my_reservations_url = f"{self.base_url}?owner={self.Owner.ME}"
        self.MAKEs_reservations_url = f"{self.base_url}?owner={self.Owner.MAKE}"

    # noinspection PyPep8Naming
    def assert_context_has(self, response, *, reservations: set[Reservation], reservations_owned_by_MAKE: bool, has_admin_perms: bool):
        self.assertEqual(response.status_code, HTTPStatus.OK)
        context = response.context
        self.assertSetEqual(set_without_duplicates(self, context['reservations']), reservations)
        self.assertEqual(context['reservations_owned_by_MAKE'], reservations_owned_by_MAKE)
        self.assertEqual(context['has_admin_perms'], has_admin_perms)

    def test_responds_with_expected_context_data_for_all_owner_param_choices(self):
        # owner=ReservationListQueryForm.Owner.MAKE
        self.assertEqual(self.user_client.get(self.MAKEs_reservations_url).status_code, HTTPStatus.FORBIDDEN)

        self.assert_context_has(self.admin_client.get(self.MAKEs_reservations_url),
                                reservations={self.special_reservation_by_admin, self.event_reservation_by_admin},
                                reservations_owned_by_MAKE=True, has_admin_perms=True)

        # owner=ReservationListQueryForm.Owner.ME
        self.assert_context_has(self.user_client.get(self.my_reservations_url),
                                reservations={self.normal_reservation_by_user, self.sewing_reservation_by_user},
                                reservations_owned_by_MAKE=False, has_admin_perms=False)
        self.assert_context_has(self.admin_client.get(self.my_reservations_url),
                                reservations={self.special_reservation_by_admin, self.normal_reservation_by_admin, self.event_reservation_by_admin,
                                              self.sewing_reservation_by_admin},
                                reservations_owned_by_MAKE=False, has_admin_perms=True)

    def test_responds_with_expected_query_parameter_errors(self):
        def assert_error_response_contains(client_: Client, *, query: str, expected_json_dict: dict):
            url = f"{self.base_url}?{query}" if query else self.base_url
            response = client_.get(url)
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertDictEqual(response.json(), expected_json_dict)

        field_required = "Feltet er påkrevet."
        qwer_invalid = "Velg et gyldig valg. qwer er ikke et av de tilgjengelige valgene."
        undefined_asdf_field = {'undefined_fields': {'message': "These provided fields are not defined in the API.", 'fields': ['asdf']}}
        for user, client in ((self.admin, self.admin_client),
                             (self.user, self.user_client)):
            with self.subTest(user=user):
                assert_error_response_contains(client, query="", expected_json_dict={
                    'field_errors': {'owner': [field_required]}})
                assert_error_response_contains(client, query="owner=qwer", expected_json_dict={
                    'field_errors': {'owner': [qwer_invalid]}})
                assert_error_response_contains(client, query="asdf=asdf", expected_json_dict={
                    'field_errors': {'owner': [field_required]}, **undefined_asdf_field})
                assert_error_response_contains(client, query="owner=qwer&asdf=asdf", expected_json_dict={
                    'field_errors': {'owner': [qwer_invalid]}, **undefined_asdf_field})
                assert_error_response_contains(client, query=f"owner={self.Owner.ME}&asdf=asdf", expected_json_dict={
                    **undefined_asdf_field})


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
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

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
