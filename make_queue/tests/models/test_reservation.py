from django.test import TestCase
from unittest.mock import patch

from make_queue.fields import MachineTypeField
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, Quota, Reservation, ReservationRule
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, datetime, time

from make_queue.util.time import local_to_date
from news.models import Event, TimePlace


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
        self.user_quota = Quota.objects.create(user=self.user, ignore_rules=False, number_of_reservations=2,
                                               machine_type=self.machine_type)
        self.course_registration = Printer3DCourse.objects.create(user=self.user, username=self.user.username,
                                                                  date=datetime.now().date(),
                                                                  name=self.user.get_full_name())
        self.max_time_reservation = 5
        ReservationRule.objects.create(machine_type=self.machine_type, start_time=time(0, 0), end_time=time(23, 59),
                                       days_changed=6, start_days=1, max_hours=self.max_time_reservation,
                                       max_inside_border_crossed=self.max_time_reservation)

    def save_past_reservation(self, reservation):
        validate_function = reservation.validate
        reservation.validate = lambda: True
        reservation.save()
        reservation.validate = validate_function

    def create_reservation(self, timedelta_start, timedelta_end, event=None, user=None, machine=None, special=False,
                           special_text=""):
        machine = self.machine if machine is None else machine
        user = self.user if user is None else user
        return Reservation(user=user, machine=machine, event=event, start_time=timezone.now() + timedelta_start,
                           end_time=timezone.now() + timedelta_end, special=special, special_text=special_text)

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

    def test_not_allowed_user_cannot_create_reservation(self):
        self.course_registration.delete()
        self.assertFalse(self.machine_type.can_user_use(self.user))
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
            "Uses that cannot use a machine, should not be able to reserve it"
        )

    def test_reserve_end_time_before_start_time(self):
        self.check_reservation_invalid(self.create_reservation(timedelta(hours=1), timedelta(minutes=30)),
                                       "Reservations should not be able to end before they start")

    def test_reserve_longer_than_maximum_user_time(self):
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=self.max_time_reservation + 1.1)),
            "Reservations should not be allowed to exceed the maximum allowed time for the user")

    def test_reserve_in_the_past(self):
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=-1), timedelta(hours=1)),
            "A reservation is invalid if it starts in the past, even though it ends in the future"
        )

        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=-1), timedelta(hours=-0.5)),
            "A reservation is invalid if it is completely in the past"
        )

    def test_make_more_than_one_reservation(self):
        self.user_quota.number_of_reservations = 5
        self.user_quota.save()

        self.assertTrue(Quota.can_make_new_reservation(self.user, self.machine_type))

        for reservation_number in range(5):
            self.check_reservation_valid(self.create_reservation(timedelta(days=reservation_number, hours=1),
                                                                 timedelta(days=reservation_number, hours=2)),
                                         "User should be able to make as many reservations as allowed")

        self.assertFalse(Quota.can_make_new_reservation(self.user, self.machine_type))

    def test_make_more_than_allowed_number_of_reservations(self):
        self.user_quota.number_of_reservations = 5
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
        self.user_quota.number_of_reservations = 3
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
            self.create_reservation(timedelta(hours=1), timedelta(hours=self.max_time_reservation + 2),
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
        additional_printer = Machine.objects.create(name="C2", location="Printer room Mackerspace U1", status="F",
                                                    machine_type=self.machine_type)
        Machine.objects.create(name="C3", location="Printer room Mackerspace U1", status="F",
                               machine_type=self.machine_type)

        self.check_reservation_valid(self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
                                     "Saving a single reservation should be valid")

        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2), machine=additional_printer),
            "Reservations on different printers should be able to overlap in time")

    def test_can_owner_change_future_reservation(self):
        self.assertTrue(self.create_reservation(timedelta(hours=1), timedelta(hours=2)).can_change(self.user))

    def test_can_owner_change_started_reservation(self):
        self.assertFalse(self.create_reservation(timedelta(hours=-1), timedelta(hours=2)).can_change(self.user))

    def test_can_owner_change_end_time_of_started_reservation(self):
        reservation = self.create_reservation(timedelta(hours=-2), timedelta(hours=2))
        self.save_past_reservation(reservation)
        self.assertTrue(reservation.can_change_end_time(self.user))
        reservation.end_time = timezone.now() + timedelta(hours=1)
        self.check_reservation_valid(reservation, "Should be able to change end time of started reservation")
        reservation.end_time = timezone.now() + timedelta(hours=-1)
        self.check_reservation_invalid(reservation,
                                       "Should not be able to change end time of started reservation to before the current time")

    def test_can_owner_change_end_time_of_ended_reservation(self):
        self.assertFalse(
            self.create_reservation(timedelta(hours=-3), timedelta(hours=-1)).can_change_end_time(self.user))

    def test_can_owner_change_started_event_reservation(self):
        self.give_user_event_permission()

        self.assertTrue(
            self.create_reservation(timedelta(hours=-1), timedelta(hours=2), event=self.timeplace).can_change(
                self.user))

    def test_can_owner_change_started_special_reservation(self):
        self.give_user_event_permission()

        self.assertTrue(self.create_reservation(timedelta(hours=-1), timedelta(hours=2), special=True,
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
        self.assertTrue(self.create_reservation(timedelta(hours=1), timedelta(hours=2)).can_delete(self.user))

    def test_cannot_delete_started_reservation(self):
        self.assertFalse(self.create_reservation(timedelta(hours=-1), timedelta(hours=2)).can_delete(self.user))

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
