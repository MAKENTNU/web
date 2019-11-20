from datetime import timedelta, time
from unittest.mock import patch

from django.contrib.auth.models import User, Permission
from django.http import HttpResponse
from django.test import TestCase
from django.utils import timezone

from make_queue.fields import MachineTypeField
from make_queue.forms import ReservationForm
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, Quota, Reservation, ReservationRule
from make_queue.tests.utility import request_with_user, post_request_with_user, template_view_get_context_data
from make_queue.util.time import date_to_local, local_to_date
from make_queue.views.admin.reservation import AdminReservationView
from make_queue.views.reservation.reservation import ReservationCreateOrChangeView, MakeReservationView, \
    ChangeReservationView, MarkReservationAsDone
from news.models import Event, TimePlace


class BaseReservationCreateOrChangeViewTest(TestCase):

    def setUp(self):
        Reservation.reservation_future_limit_days = 7
        self.machine_type_sewing = MachineTypeField.get_machine_type(2)
        self.user = User.objects.create_user(username="test")
        self.machine = Machine.objects.create(machine_model="Test", machine_type=self.machine_type_sewing)
        self.event = Event.objects.create(title="Test_event")
        Quota.objects.create(user=self.user, machine_type=self.machine_type_sewing, number_of_reservations=100,
                             ignore_rules=True)
        self.timeplace = TimePlace.objects.create(event=self.event,
                                                  start_time=(timezone.now() + timedelta(hours=1)).time(),
                                                  start_date=(timezone.now() + timedelta(hours=1)).date(),
                                                  end_time=(timezone.now() + timedelta(hours=2)).time(),
                                                  end_date=(timezone.now() + timedelta(hours=2)).date())

    def get_view(self):
        view = ReservationCreateOrChangeView()
        view.request = request_with_user(self.user)
        return view

    def create_form(self, start_diff, end_diff, event=None, special=False, special_text=""):
        return ReservationForm(data=self.create_form_data(start_diff, end_diff, event, special, special_text))

    def create_form_data(self, start_diff, end_diff, event=None, special=False, special_text=""):
        return {
            "start_time": date_to_local(timezone.now() + timedelta(hours=start_diff)).strftime("%d.%m.%Y %H:%M:%S"),
            "end_time": date_to_local(timezone.now() + timedelta(hours=end_diff)).strftime("%d.%m.%Y %H:%M:%S"),
            "event": event is not None, "event_pk": 0 if event is None else event.pk, "special": special,
            "special_text": special_text, "machine_name": self.machine.pk
        }


class ReservationCreateOrChangeViewTest(BaseReservationCreateOrChangeViewTest):

    def test_get_error_message_non_event(self):
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        reservation = Reservation(user=self.user, start_time=form.cleaned_data["start_time"],
                                  end_time=form.cleaned_data["end_time"], machine=self.machine)
        self.assertEqual(view.get_error_message(form, reservation), "The time slot is not available")

    def test_get_error_message_event(self):
        view = self.get_view()
        form = self.create_form(1, 2, event=self.event)
        self.assertTrue(form.is_valid())
        reservation = Reservation(user=self.user, start_time=form.cleaned_data["start_time"],
                                  end_time=form.cleaned_data["end_time"], machine=self.machine)
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        self.assertEqual(view.get_error_message(form, reservation),
                         "The time slot or event, it no longer available")

    def test_get_error_message_too_far_in_the_future(self):
        view = self.get_view()
        form = self.create_form(24 * 7, 24 * 7 + 1)
        self.assertTrue(form.is_valid())
        reservation = Reservation(user=self.user, start_time=form.cleaned_data["start_time"],
                                  end_time=form.cleaned_data["end_time"], machine=self.machine)
        self.assertEqual(view.get_error_message(form, reservation),
                         "Reservations can only be made 7 days ahead of time")

    def test_validate_and_save_valid_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        reservation = Reservation(user=self.user, start_time=form.cleaned_data["start_time"],
                                  end_time=form.cleaned_data["end_time"], machine=self.machine)
        response = view.validate_and_save(reservation, form)
        self.assertEqual(1, Reservation.objects.count())
        self.assertEqual(302, response.status_code)

    def test_validate_and_save_non_valid_reservation(self):
        view = self.get_view()
        # Set values to allow for context to be created
        view.new_reservation = False

        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        # Test with collision
        Reservation.objects.create(user=self.user, start_time=form.cleaned_data["start_time"],
                                   end_time=form.cleaned_data["end_time"], machine=self.machine)
        reservation = Reservation(user=self.user, start_time=form.cleaned_data["start_time"],
                                  end_time=form.cleaned_data["end_time"], machine=self.machine)
        response = view.validate_and_save(reservation, form)
        # Second reservation should not be saved
        self.assertEqual(1, Reservation.objects.count())
        # 200 to re render the form
        self.assertEqual(200, response.status_code)

    def test_get_context_data_reservation(self):
        view = self.get_view()
        view.new_reservation = False
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        reservation = Reservation.objects.create(user=self.user, start_time=timezone.now() + timedelta(hours=1),
                                                 end_time=timezone.now() + timedelta(hours=2),
                                                 event=self.timeplace, machine=self.machine, comment="Comment")
        context_data = view.get_context_data(reservation=reservation)
        context_data["machine_types"] = [
            {"literal": machine_type["literal"], "instances": list(machine_type["instances"])} for machine_type in
            context_data["machine_types"]]

        self.assertEqual(context_data, {
            "can_change_start_time": True, "events": [self.timeplace], "new_reservation": False, "machine_types": [{
                "literal": machine_type.name,
                "instances": list(Machine.objects.filter(machine_type=machine_type))
            } for machine_type in MachineTypeField.possible_machine_types if machine_type.can_user_use(self.user)
            ],
            "start_time": reservation.start_time, "end_time": reservation.end_time, "selected_machine": self.machine,
            "event": self.timeplace, "special": False, "special_text": "",
            "maximum_days_in_advance": Reservation.reservation_future_limit_days, "comment": "Comment",
            "reservation_pk": reservation.pk
        })

    def test_get_context_data_non_reservation(self):
        view = self.get_view()
        view.new_reservation = True
        start_time = timezone.now() + timedelta(hours=1)
        context_data = view.get_context_data(machine=self.machine, start_time=start_time)

        context_data["machine_types"] = [
            {"literal": machine_type["literal"], "instances": list(machine_type["instances"])} for machine_type in
            context_data["machine_types"]]
        self.assertEqual(context_data, {
            "can_change_start_time": True,
            "events": [self.timeplace], "new_reservation": True,
            "machine_types": [{
                "literal": machine_type.name,
                "instances": list(Machine.objects.filter(machine_type=machine_type))
            } for machine_type in MachineTypeField.possible_machine_types if machine_type.can_user_use(self.user)
            ],
            "start_time": start_time, "selected_machine": self.machine,
            "maximum_days_in_advance": Reservation.reservation_future_limit_days,
        })

    def test_post_valid_form(self):
        view = self.get_view()
        view.request = post_request_with_user(self.user, data=self.create_form_data(1, 2))
        # Set values to allow for context to be created
        view.new_reservation = False
        # Need to handle the valid form function
        valid_form_calls = {"calls": 0}
        view.form_valid = lambda x, **y: valid_form_calls.update(
            {"calls": valid_form_calls["calls"] + 1}) or HttpResponse()

        self.assertTrue(ReservationForm(view.request.POST).is_valid())
        response = view.handle_post(view.request)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, valid_form_calls["calls"])


class MakeReservationViewTest(BaseReservationCreateOrChangeViewTest):

    def get_view(self):
        view = MakeReservationView()
        view.request = request_with_user(self.user)
        return view

    def test_form_valid_normal_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        view.form_valid(form)
        self.assertTrue(Machine.objects.count(), 1)

    def test_form_valid_event_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2, event=self.timeplace)
        self.assertTrue(form.is_valid())
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view.form_valid(form)
        self.assertTrue(Machine.objects.count(), 1)

    def test_form_valid_special_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2, special=True, special_text="Test special")
        self.assertTrue(form.is_valid())
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view.form_valid(form)
        self.assertTrue(Machine.objects.count(), 1)

    def test_form_valid_invalid_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        Reservation.objects.create(user=self.user, start_time=form.cleaned_data["start_time"],
                                   end_time=form.cleaned_data["end_time"], machine=self.machine)
        response = view.form_valid(form)
        # Second reservation should not have been saved
        self.assertTrue(Machine.objects.count(), 1)
        # Re-rendering of form
        self.assertEqual(response.status_code, 200)


class ChangeReservationViewTest(BaseReservationCreateOrChangeViewTest):

    def get_view(self):
        view = ChangeReservationView()
        view.request = request_with_user(self.user)
        return view

    def create_reservation(self, form):
        self.assertTrue(form.is_valid())
        return Reservation.objects.create(user=self.user, start_time=form.cleaned_data["start_time"],
                                          end_time=form.cleaned_data["end_time"], machine=self.machine)

    def test_post_changeable_reservation(self):
        view = self.get_view()
        view.request.method = "POST"
        reservation = self.create_reservation(self.create_form(1, 2))
        response = view.dispatch(view.request, reservation=reservation)
        # Response should be the edit page for the reservation, as no form is posted with the data
        self.assertEqual(200, response.status_code)
        self.assertEqual(["make_queue/make_reservation.html"], response.template_name)

    @patch("django.utils.timezone.now")
    def test_post_unchangeable_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        view = self.get_view()
        view.request.method = "POST"
        reservation = self.create_reservation(self.create_form(1, 2))
        now_mock.return_value = timezone.now() + timedelta(hours=2, minutes=1)
        response = view.dispatch(view.request, reservation=reservation)
        # An unchangeable reservation should have redirect
        self.assertEqual(302, response.status_code)

    @patch("django.utils.timezone.now")
    def test_form_valid_normal_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        view = self.get_view()
        reservation = self.create_reservation(self.create_form(1, 2))
        form = self.create_form(1, 3)
        self.assertTrue(form.is_valid())
        response = view.form_valid(form, reservation=reservation)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(Reservation.objects.first().end_time, timezone.now() + timedelta(hours=3))

    @patch("django.utils.timezone.now")
    def test_form_valid_changed_machine(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        view = self.get_view()
        reservation = self.create_reservation(self.create_form(1, 2))
        old_machine = self.machine
        self.machine = Machine.objects.create(name="M1", machine_model="Generic", machine_type=self.machine_type_sewing)
        form = self.create_form(1, 3)
        self.assertTrue(form.is_valid())
        response = view.form_valid(form, reservation=reservation)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Reservation.objects.first().end_time, timezone.now() + timedelta(hours=2))
        self.assertEqual(Reservation.objects.first().machine, old_machine)

    @patch("django.utils.timezone.now")
    def test_form_valid_event_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view = self.get_view()
        reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=1),
                                                 machine=self.machine, event=self.timeplace,
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user)
        self.timeplace = TimePlace.objects.create(event=self.event,
                                                  start_time=(timezone.now() + timedelta(hours=1)).time(),
                                                  start_date=(timezone.now() + timedelta(hours=1)).date(),
                                                  end_time=(timezone.now() + timedelta(hours=2)).time(),
                                                  end_date=(timezone.now() + timedelta(hours=2)).date())
        form = self.create_form(1, 2, event=self.timeplace)
        self.assertTrue(form.is_valid())
        response = view.form_valid(form, reservation=reservation)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(Reservation.objects.first().event, self.timeplace)

    @patch("django.utils.timezone.now")
    def test_form_valid_special_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view = self.get_view()
        reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=1),
                                                 machine=self.machine, special=True,
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user,
                                                 special_text="Test")
        form = self.create_form(1, 2, special=True, special_text="Test2")
        self.assertTrue(form.is_valid())
        response = view.form_valid(form, reservation=reservation)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(Reservation.objects.first().special_text, "Test2")


class ReservationAdminViewTest(TestCase):

    def test_get_admin_reservation(self):
        user = User.objects.create_user("test")
        machine_type = MachineTypeField.get_machine_type(1)
        Quota.objects.create(machine_type=machine_type, number_of_reservations=10, ignore_rules=True, user=user)
        permission = Permission.objects.get(codename="can_create_event_reservation")
        user.user_permissions.add(permission)
        event = Event.objects.create(title="Test_event")
        timeplace = TimePlace.objects.create(event=event, start_time=(timezone.now() + timedelta(hours=1)).time(),
                                             start_date=(timezone.now() + timedelta(hours=1)).date(),
                                             end_time=(timezone.now() + timedelta(hours=2)).time(),
                                             end_date=(timezone.now() + timedelta(hours=2)).date())
        printer = Machine.objects.create(machine_type=machine_type, machine_model="Ultimaker")
        Printer3DCourse.objects.create(user=user, username=user.username, name=user.get_full_name(),
                                       date=timezone.now())
        special_reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=1),
                                                         special_text="Test", special=True, user=user,
                                                         machine=printer, end_time=timezone.now() + timedelta(hours=2))
        normal_reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=2), user=user,
                                                        machine=printer, end_time=timezone.now() + timedelta(hours=3))
        event_reservation = Reservation.objects.create(start_time=timezone.now() + timedelta(hours=3), event=timeplace,
                                                       user=user, machine=printer,
                                                       end_time=timezone.now() + timedelta(hours=4))

        context_data = template_view_get_context_data(AdminReservationView, request_user=user)
        self.assertEqual(context_data["admin"], True)
        self.assertEqual(set(context_data["reservations"]), {special_reservation, event_reservation})


class MarkReservationAsDoneTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("test")
        self.machine_type = MachineTypeField.get_machine_type(2)
        self.machine = Machine.objects.create(machine_type=self.machine_type, status="F", name="Test")
        Quota.objects.create(machine_type=self.machine_type, number_of_reservations=2, ignore_rules=False,
                             all=True)
        ReservationRule.objects.create(start_time=time(0, 0), end_time=time(23, 59), start_days=1, days_changed=6,
                                       max_inside_border_crossed=6, max_hours=6, machine_type=self.machine_type)

    def get_view(self):
        view = MarkReservationAsDone()
        view.request = request_with_user(self.user)
        return view

    def post_to_view(self, reservation):
        view = self.get_view()
        request = post_request_with_user(self.user, {"pk": reservation.pk})
        return view.post(request)

    def test_get(self):
        view = self.get_view()
        request = request_with_user(self.user)
        response = view.get(request)

        # Get is not allowed, so a redirect will be given
        self.assertEqual(302, response.status_code)

    @patch("django.utils.timezone.now")
    def test_post_valid(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=1),
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user)
        now_mock.return_value = timezone.now() + timedelta(hours=1.1)
        self.assertTrue(reservation.can_change_end_time(self.user))
        response = self.post_to_view(reservation)

        # Will always be redirected
        self.assertEqual(302, response.status_code)
        self.assertEqual(Reservation.objects.get(pk=reservation.pk).end_time, timezone.now())

    def test_post_before_start(self):
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=1),
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user)

        response = self.post_to_view(reservation)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reservation, Reservation.objects.get(pk=reservation.pk),
                         "Marking a reservation in the future as done, should not be possible")

    @patch("django.utils.timezone.now")
    def test_post_after_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=1),
                                                 end_time=timezone.now() + timedelta(hours=2), user=self.user)
        now_mock.return_value = timezone.now() + timedelta(hours=3)
        response = self.post_to_view(reservation)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reservation, Reservation.objects.get(pk=reservation.pk),
                         "Marking a reservation in the past as done should not do anything")

    @patch("django.utils.timezone.now")
    def test_special_case(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 11, 16, 10, 0, 0))
        reservation = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(minutes=1),
                                                 end_time=timezone.now() + timedelta(hours=6), user=self.user)
        reservation2 = Reservation.objects.create(machine=self.machine, start_time=timezone.now() + timedelta(hours=6),
                                                  end_time=timezone.now() + timedelta(hours=6, minutes=26),
                                                  user=User.objects.create_user("test2"))
        now_mock.return_value = local_to_date(timezone.datetime(2018, 11, 16, 15, 56, 0))
        response = self.post_to_view(reservation)
        self.assertEqual(302, response.status_code)
        self.assertEqual(timezone.now(), Reservation.objects.get(pk=reservation.pk).end_time)
