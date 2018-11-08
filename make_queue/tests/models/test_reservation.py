from django.test import TestCase
from unittest.mock import patch

from make_queue.fields import MachineTypeField
from make_queue.models.models import Machine, Quota, Reservation
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, datetime

from make_queue.util.time import local_to_date
from news.models import Event, TimePlace

"""
class GeneralReservationTestCase(TestCase):

    def check_reservation_invalid(self, reservation, error_message):
        self.assertFalse(reservation.validate(), error_message)
        try:
            reservation.save()
            self.fail(error_message)
        except ValidationError:
            pass

    def check_reservation_valid(self, reservation, error_message):
        self.assertTrue(reservation.validate(), error_message)
        try:
            reservation.save()
        except ValidationError:
            self.fail(error_message)


class GeneralReservationTestCases(GeneralReservationTestCase):
    def setUp(self):
        event = Event.objects.create(title="TEST EVENT")
        self.timeplace = TimePlace.objects.create(pub_date=timezone.now(), start_date=timezone.now(),
                                                  start_time=(timezone.now() + timedelta(seconds=1)).time(),
                                                  event=event)
        self.machine_type = MachineTypeField.get_machine_type(1)
        self.machine = Machine.objects.create(name="C1", location="Printer room", status="F",
                                              machine_type=self.machine_type)
        self.user = User.objects.create_user("User", "user@makentnu.no", "user_pass")
        self.user_quota = Quota.objects.create(user=self.user, can_print=True, ignore_rules=False,
                                               max_number_of_reservations=2, machine_type=self.machine_type)

    def create_reservation(self, timedelta_start, timedelta_end, event=None, user=None, machine=None, special=False,
                           special_text=""):
        machine = self.machine if machine is None else machine
        user = self.user if user is None else user
        return Reservation3D(user=user, machine=machine, event=event, start_time=timezone.now() + timedelta_start,
                             end_time=timezone.now() + timedelta_end, special=special, special_text=special_text)

    def set_percentage_of_maximum_machines(self, percentage):
        self.max_percentage = Reservation3D.percentage_of_machines_at_the_same_time
        Reservation3D.percentage_of_machines_at_the_same_time = percentage

    def reset_percentage_of_maximum_machines(self):
        Reservation3D.percentage_of_machines_at_the_same_time = self.max_percentage

    def set_reservation_future_limit_days(self, days):
        self.reservation_future_limit_days = Reservation.reservation_future_limit_days
        Reservation.reservation_future_limit_days = days

    def reset_reservation_future_limit_days(self):
        Reservation.reservation_future_limit_days = self.reservation_future_limit_days

    def give_user_event_permission(self):
        self.user.user_permissions.add(Permission.objects.get(name="Can create event reservation"))

    def test_can_create_reservation(self):
        self.check_reservation_valid(self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
                                     "Reservations should be saveable")

    def test_reserve_end_time_before_start_time(self):
        self.check_reservation_invalid(self.create_reservation(timedelta(hours=1), timedelta(minutes=30)),
                                       "Reservations should not be able to end before they start")

    def test_reserve_longer_than_maximum_user_time(self):
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=self.user_quota.max_time_reservation + 1.1)),
            "Reservations should not be allowed to exceed the maximum allowed time for the user")

    def test_make_more_than_one_reservation(self):
        self.user_quota.max_number_of_reservations = 5
        self.user_quota.save()

        for reservation_number in range(5):
            self.check_reservation_valid(self.create_reservation(timedelta(days=reservation_number, hours=1),
                                                                 timedelta(days=reservation_number, hours=2)),
                                         "User should be able to make as many reservations as allowed")

    def test_make_more_than_allowed_number_of_reservations(self):
        self.user_quota.max_number_of_reservations = 5
        self.user_quota.save()

        for reservation_number in range(5):
            self.check_reservation_valid(self.create_reservation(timedelta(days=reservation_number, hours=1),
                                                                 timedelta(days=reservation_number, hours=2)),
                                         "User should be able to make as many reservations as allowed")

        self.check_reservation_invalid(self.create_reservation(timedelta(days=5, hours=1), timedelta(days=5, hours=2)),
                                       "User should not be able to make more reservations than allowed")

    @patch("django.utils.timezone.now")
    def test_disallow_overlapping_reservations(self, now_mock):
        now_mock.return_value = local_to_date(datetime(2018, 3, 12, 12, 0, 0))
        self.user_quota.max_number_of_reservations = 3
        self.user_quota.save()

        self.check_reservation_valid(self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
                                     "Saving should be valid")

        # Start before, end inside
        self.check_reservation_invalid(self.create_reservation(timedelta(minutes=50), timedelta(hours=1, minutes=50)),
                                       "Reservation should not be able to end inside another")

        # Start inside, end after
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1, minutes=10), timedelta(hours=2, minutes=10)),
            "Reservation should not be able to end inside another")

        # Start inside, end inside
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1, minutes=10), timedelta(hours=1, minutes=50)),
            "Reservation should not be able to start and end inside another")

        # Start before, end after
        self.check_reservation_invalid(self.create_reservation(timedelta(minutes=50), timedelta(hours=2, minutes=10)),
                                       "Reservation should not be able to encapsulate another")

        # End at the start time of other
        self.check_reservation_valid(self.create_reservation(timedelta(hours=0), timedelta(hours=1)),
                                     "A reservation should be allowed to end at the same time another one starts")

        # Start at the end time of other
        self.check_reservation_valid(self.create_reservation(timedelta(hours=2), timedelta(hours=3)),
                                     "A reservation should be allowed to start at the same time another one ends")

    def test_make_event_without_event_permission(self):
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2), event=self.timeplace),
            "Should not be able to make event reservation without correct permission")

    def test_make_event_with_event_permission(self):
        self.give_user_event_permission()
        self.user_quota.max_number_of_reservations = 1
        self.user_quota.save()

        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2), event=self.timeplace),
            "User with the correct permission should be allowed to create an event reservation")

        self.check_reservation_valid(
            self.create_reservation(timedelta(days=1, hours=1), timedelta(days=1, hours=2), event=self.timeplace),
            "Event reservations should not count towards the total number of reservations")

    def test_make_event_reservation_with_longer_than_user_max_time(self):
        self.give_user_event_permission()

        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=self.user_quota.max_time_reservation + 2),
                                    event=self.timeplace),
            "User should be able to make event reservations longer than their maximum reservation time")

    def test_change_event_while_maximum_booked(self):
        self.user_quota.max_number_of_reservations = 1
        self.user_quota.save()

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))

        self.check_reservation_valid(reservation, "Reservation should be valid")

        reservation.end_time = timezone.now() + timedelta(hours=3)

        self.check_reservation_valid(reservation,
                                     "Changing a reservation with the maximum number of reservations should be valid")

    def test_same_time_separate_machines(self):
        additional_printer = Printer3D.objects.create(name="C2", location="Printer room Mackerspace U1", status="F")
        self.set_percentage_of_maximum_machines(1)
        Printer3D.objects.create(name="C3", location="Printer room Mackerspace U1", status="F")

        self.check_reservation_valid(self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
                                     "Saving a single reservation should be valid")

        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2), machine=additional_printer),
            "Reservations on different printers should be able to overlap in time")

        self.reset_percentage_of_maximum_machines()

    def test_same_time_separate_machines_more_than_allowed(self):
        additional_printer = Printer3D.objects.create(name="C2", location="Printer room Mackerspace U1", status="F")
        self.set_percentage_of_maximum_machines(0.5)

        self.check_reservation_valid(self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
                                     "Saving a single reservation should be valid")

        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2), machine=additional_printer),
            "User should not be able to reserve more than 50% of the printers")

        self.reset_percentage_of_maximum_machines()

    def test_can_owner_change_future_reservation(self):
        self.assertTrue(self.create_reservation(timedelta(hours=1), timedelta(hours=2)).can_change(self.user))

    def test_can_owner_change_started_reservation(self):
        self.assertFalse(self.create_reservation(timedelta(hours=-1), timedelta(hours=2)).can_change(self.user))

    def test_can_owner_change_started_event_reservation(self):
        self.give_user_event_permission()

        self.assertFalse(
            self.create_reservation(timedelta(hours=-1), timedelta(hours=2), event=self.timeplace).can_change(
                self.user))

    def test_can_owner_change_started_special_reservation(self):
        self.give_user_event_permission()

        self.assertFalse(self.create_reservation(timedelta(hours=-1), timedelta(hours=2), special=True,
                                                 special_text="Test").can_change(self.user))

    def test_can_other_user_change_future_reservation(self):
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))

        self.assertTrue(reservation.can_change(self.user))
        self.assertFalse(reservation.can_change(user2))

    def test_can_user_with_event_reservation_change_other_user_non_event_reservation(self):
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        user2.user_permissions.add(Permission.objects.get(name="Can create event reservation"))

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))

        self.assertTrue(reservation.can_change(self.user))
        self.assertFalse(reservation.can_change(user2))

    def test_can_user_with_event_reservation_change_other_user_event_reservation(self):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        user2.user_permissions.add(Permission.objects.get(name="Can create event reservation"))

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2), event=self.timeplace)

        self.assertTrue(reservation.can_change(self.user))
        self.assertTrue(reservation.can_change(user2))

    def test_can_user_with_event_reservation_change_other_user_special_reservation(self):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        user2.user_permissions.add(Permission.objects.get(name="Can create event reservation"))

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2), special=True, special_text="Test")

        self.assertTrue(reservation.can_change(self.user))
        self.assertTrue(reservation.can_change(user2))

    def test_can_user_without_event_reservation_change_other_user_special_reservation(self):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2), special=True, special_text="Test")

        self.assertTrue(reservation.can_change(self.user))
        self.assertFalse(reservation.can_change(user2))

    def test_can_user_without_event_reservation_change_other_user_event_reservation(self):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2), event=self.timeplace)

        self.assertTrue(reservation.can_change(self.user))
        self.assertFalse(reservation.can_change(user2))

    def test_can_delete_future_reservation(self):
        self.assertTrue(self.create_reservation(timedelta(hours=1), timedelta(hours=2)).can_delete())

    def test_cannot_delete_started_reservation(self):
        self.assertFalse(self.create_reservation(timedelta(hours=-1), timedelta(hours=2)).can_delete())

    def test_has_reached_maximum_number_of_reservations(self):
        additional_printer = Printer3D.objects.create(name="C2")
        self.set_percentage_of_maximum_machines(0.4)
        reservation = Reservation3D.objects.create(user=self.user, start_time=timezone.now() + timedelta(hours=1),
                                                   machine=self.machine, end_time=timezone.now() + timedelta(hours=2))
        self.assertFalse(reservation.has_reached_maximum_number_of_reservations())
        reservation2 = self.create_reservation(timedelta(hours=1), timedelta(hours=2), machine=additional_printer)
        self.assertTrue(reservation2.has_reached_maximum_number_of_reservations())
        self.reset_percentage_of_maximum_machines()

    def test_is_within_allowed_period_for_reservation(self):
        self.set_reservation_future_limit_days(7)
        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))
        self.assertTrue(reservation.is_within_allowed_period_for_reservation())
        reservation.end_time = timezone.now() + timedelta(days=7, minutes=2)
        self.assertFalse(reservation.is_within_allowed_period_for_reservation())
        self.reset_reservation_future_limit_days()

    def test_make_reservation_too_far_in_the_future(self):
        self.set_reservation_future_limit_days(7)
        self.check_reservation_invalid(self.create_reservation(timedelta(days=7), timedelta(days=7, hours=1)),
                                       "Reservation is too far in the future and should not be valid")
        self.reset_reservation_future_limit_days()

    def test_make_event_reservation_too_far_in_the_future(self):
        self.set_reservation_future_limit_days(7)
        self.give_user_event_permission()
        self.check_reservation_valid(
            self.create_reservation(timedelta(days=7), timedelta(days=7, hours=1), event=self.timeplace),
            "Event reservations are always valid no matter how far in the future they are")
        self.reset_reservation_future_limit_days()


class ReservationSewingTestCase(GeneralReservationTestCase):
    def setUp(self):
        SewingMachine.objects.create(name="C1", location="Makerspace U1", status="F", model="Generic")
        user = User.objects.create_user("User", "user@makentnu.no", "user_pass")
        user.save()
        QuotaSewing.objects.create(user=user, max_time_reservation=10, max_number_of_reservations=2)

    def test_user_can_reserve_sewing_machine(self):
        sewing_machine = SewingMachine.objects.get(name="C1")
        user = User.objects.get(username="User")

        user_quota = user.quotasewing
        user_quota.max_number_of_reservations = 2
        user_quota.save()

        reservation = ReservationSewing(user=user, machine=sewing_machine, start_time=timezone.now(),
                                        end_time=timezone.now() + timedelta(hours=2), event=None)

        self.check_reservation_valid(reservation, "Users should be able to reserve sewing machines")


class Reservation3DTestCase(GeneralReservationTestCase):
    def setUp(self):
        Printer3D.objects.create(name="C1", location="Printer room Makerspace U1", status="F", model="Ultimaker 2")
        SewingMachine.objects.create(name="S1", location="Mackerspace U1 main room", status="F")
        user = User.objects.create_user("User", "user@makentnu.no", "user_pass")
        user.save()
        Quota3D.objects.create(user=user, can_print=True, max_time_reservation=10, max_number_of_reservations=2)
        QuotaSewing.objects.create(user=user, max_time_reservation=10, max_number_of_reservations=2)

    def test_user_that_cannot_print_cannot_reserve(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")
        user_quota = user.quota3d
        user_quota.can_print = False
        user_quota.save()

        reservation = Reservation3D(user=user, machine=printer,
                                    start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=2),
                                    event=None)

        self.check_reservation_invalid(reservation, "Users that cannot print, should not be able to reserve printer")
"""
