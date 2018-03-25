import json
from datetime import timedelta

from django.contrib.auth.models import User, Permission
from django.http import HttpResponse
from django.test import TestCase
from django.utils import timezone
from mock import patch

from make_queue.forms import ReservationForm
from make_queue.models import SewingMachine, ReservationSewing, QuotaSewing
from make_queue.tests.utility import request_with_user, post_request_with_user
from make_queue.util.time import date_to_local, local_to_date
from make_queue.views.reservation.reservation import ReservationCreateOrChangeView, MakeReservationView, \
    ChangeReservationView
from news.models import Event, TimePlace


class BaseReservationCreateOrChangeViewTest(TestCase):

    def setUp(self):
        ReservationSewing.percentage_of_machines_at_the_same_time = 1
        self.user = User.objects.create_user(username="test")
        self.machine = SewingMachine.objects.create(model="Test")
        self.event = Event.objects.create(title="Test_event")
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
            "special_text": special_text, "machine_type": SewingMachine.literal, "machine_name": self.machine.pk
        }


class ReservationCreateOrChangeViewTest(BaseReservationCreateOrChangeViewTest):

    def test_get_error_message_non_event(self):
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        reservation = ReservationSewing(user=self.user, start_time=form.cleaned_data["start_time"],
                                        end_time=form.cleaned_data["end_time"], machine=self.machine)
        self.assertEqual(view.get_error_message(form, reservation), "Tidspunktet er ikke lengre tilgjengelig")

    def test_get_error_message_event(self):
        view = self.get_view()
        form = self.create_form(1, 2, event=self.event)
        self.assertTrue(form.is_valid())
        reservation = ReservationSewing(user=self.user, start_time=form.cleaned_data["start_time"],
                                        end_time=form.cleaned_data["end_time"], machine=self.machine)
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        self.assertEqual(view.get_error_message(form, reservation),
                         "Tidspunktet eller eventen, er ikke lengre tilgjengelig")

    def test_get_error_message_maximum_reached(self):
        ReservationSewing.percentage_of_machines_at_the_same_time = 0
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        reservation = ReservationSewing(user=self.user, start_time=form.cleaned_data["start_time"],
                                        end_time=form.cleaned_data["end_time"], machine=self.machine)
        self.assertEqual(view.get_error_message(form, reservation),
                         "Du har booket maksimalt antall reservasjoner for denne tidsperioden, prøv et annet tidspunkt")

    def test_validate_and_save_valid_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        reservation = ReservationSewing(user=self.user, start_time=form.cleaned_data["start_time"],
                                        end_time=form.cleaned_data["end_time"], machine=self.machine)
        response = view.validate_and_save(reservation, form)
        self.assertEqual(1, ReservationSewing.objects.count())
        self.assertEqual(302, response.status_code)

    def test_validate_and_save_non_valid_reservation(self):
        view = self.get_view()
        # Set values to allow for context to be created
        view.new_reservation = False
        view.sub_class = SewingMachine

        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        # Test with collision
        ReservationSewing.objects.create(user=self.user, start_time=form.cleaned_data["start_time"],
                                         end_time=form.cleaned_data["end_time"], machine=self.machine)
        reservation = ReservationSewing(user=self.user, start_time=form.cleaned_data["start_time"],
                                        end_time=form.cleaned_data["end_time"], machine=self.machine)
        response = view.validate_and_save(reservation, form)
        # Second reservation should not be saved
        self.assertEqual(1, ReservationSewing.objects.count())
        # 200 to re render the form
        self.assertEqual(200, response.status_code)

    def test_get_context_data_reservation(self):
        view = self.get_view()
        view.new_reservation = False
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        reservation = ReservationSewing.objects.create(user=self.user, start_time=timezone.now() + timedelta(hours=1),
                                                       end_time=timezone.now() + timedelta(hours=2),
                                                       event=self.timeplace, machine=self.machine)
        context_data = view.get_context_data(reservation=reservation)

        self.assertEqual(context_data, {
            "events": [self.timeplace], "new_reservation": False, "machine_types": [{"literal": SewingMachine.literal,
                                                                                     "instances": [self.machine]}],
            "start_time": reservation.start_time, "end_time": reservation.end_time, "selected_machine": self.machine,
            "event": self.timeplace, "special": False, "special_text": "", "quota": QuotaSewing.get_quota(self.user),
        })

    def test_get_context_data_non_reservation(self):
        view = self.get_view()
        view.new_reservation = True
        start_time = timezone.now() + timedelta(hours=1)
        context_data = view.get_context_data(machine=self.machine, start_time=start_time)

        self.assertEqual(context_data, {
            "events": [self.timeplace], "new_reservation": True, "machine_types": [{"literal": SewingMachine.literal,
                                                                                    "instances": [self.machine]}],
            "start_time": start_time, "selected_machine": self.machine, "quota": QuotaSewing.get_quota(self.user)
        })

    def test_post_valid_form(self):
        view = self.get_view()
        view.request = post_request_with_user(self.user, data=self.create_form_data(1, 2))
        # Set values to allow for context to be created
        view.new_reservation = False
        view.sub_class = SewingMachine
        # Need to handle the valid form function
        valid_form_calls = {"calls": 0}
        view.form_valid = lambda x, **y: valid_form_calls.update(
            {"calls": valid_form_calls["calls"] + 1}) or HttpResponse()

        self.assertTrue(ReservationForm(view.request.POST).is_valid())
        response = view.handle_post(view.request)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, valid_form_calls["calls"])

    def test_post_invalid_form(self):
        view = self.get_view()
        view.request = post_request_with_user(self.user, data=self.create_form_data(-1, 2))
        # Set values to allow for context to be created
        view.new_reservation = False
        view.sub_class = SewingMachine
        # Need to handle the valid form function, which should never be called
        view.form_valid = lambda x, **y: self.fail("Valid form should never be called with an invalid form")

        self.assertFalse(ReservationForm(view.request.POST).is_valid())
        response = view.handle_post(view.request, machine=self.machine)
        self.assertEqual(200, response.status_code)


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
        self.assertTrue(SewingMachine.objects.count(), 1)

    def test_form_valid_event_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2, event=self.timeplace)
        self.assertTrue(form.is_valid())
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view.form_valid(form)
        self.assertTrue(SewingMachine.objects.count(), 1)

    def test_form_valid_special_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2, special=True, special_text="Test special")
        self.assertTrue(form.is_valid())
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view.form_valid(form)
        self.assertTrue(SewingMachine.objects.count(), 1)

    def test_form_valid_invalid_reservation(self):
        view = self.get_view()
        form = self.create_form(1, 2)
        self.assertTrue(form.is_valid())
        ReservationSewing.objects.create(user=self.user, start_time=form.cleaned_data["start_time"],
                                         end_time=form.cleaned_data["end_time"], machine=self.machine)
        response = view.form_valid(form)
        # Second reservation should not have been saved
        self.assertTrue(SewingMachine.objects.count(), 1)
        # Re-rendering of form
        self.assertEqual(response.status_code, 200)


class ChangeReservationViewTest(BaseReservationCreateOrChangeViewTest):

    def get_view(self):
        view = ChangeReservationView()
        view.request = request_with_user(self.user)
        return view

    def create_reservation(self, form):
        self.assertTrue(form.is_valid())
        return ReservationSewing.objects.create(user=self.user, start_time=form.cleaned_data["start_time"],
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
        self.assertEqual(ReservationSewing.objects.count(), 1)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(ReservationSewing.objects.first().end_time, timezone.now() + timedelta(hours=3))

    @patch("django.utils.timezone.now")
    def test_form_valid_changed_machine(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        view = self.get_view()
        reservation = self.create_reservation(self.create_form(1, 2))
        old_machine = self.machine
        self.machine = SewingMachine.objects.create(model="Generic")
        form = self.create_form(1, 3)
        self.assertTrue(form.is_valid())
        response = view.form_valid(form, reservation=reservation)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(ReservationSewing.objects.count(), 1)
        self.assertEqual(ReservationSewing.objects.first().end_time, timezone.now() + timedelta(hours=2))
        self.assertEqual(ReservationSewing.objects.first().get_machine(), old_machine)

    @patch("django.utils.timezone.now")
    def test_form_valid_event_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view = self.get_view()
        reservation = ReservationSewing.objects.create(start_time=timezone.now() + timedelta(hours=1),
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
        self.assertEqual(ReservationSewing.objects.count(), 1)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(ReservationSewing.objects.first().event, self.timeplace)

    @patch("django.utils.timezone.now")
    def test_form_valid_special_reservation(self, now_mock):
        now_mock.return_value = local_to_date(timezone.datetime(2018, 8, 12, 12, 0, 0))
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))
        view = self.get_view()
        reservation = ReservationSewing.objects.create(start_time=timezone.now() + timedelta(hours=1),
                                                       machine=self.machine, special=True,
                                                       end_time=timezone.now() + timedelta(hours=2), user=self.user,
                                                       special_text="Test")
        form = self.create_form(1, 2, special=True, special_text="Test2")
        self.assertTrue(form.is_valid())
        response = view.form_valid(form, reservation=reservation)
        self.assertEqual(ReservationSewing.objects.count(), 1)
        self.assertTrue(response.status_code, 302)
        self.assertEqual(ReservationSewing.objects.first().special_text, "Test2")
