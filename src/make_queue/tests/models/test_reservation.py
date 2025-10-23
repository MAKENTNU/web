from abc import ABC
from collections.abc import Callable
from datetime import datetime, timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_time

from news.models import Event, TimePlace
from users.models import User
from util.locale_utils import parse_datetime_localized
from ...models.course import CoursePermission, Printer3DCourse
from ...models.machine import Machine, MachineType
from ...models.reservation import Quota, Reservation, ReservationRule
from ...templatetags.reservation_extra import can_change_reservation


Day = ReservationRule.Day


class ReservationTestBase(TestCase, ABC):
    def init_objs(self, machine_type: MachineType):
        self.machine_type = machine_type
        self.machine = Machine.objects.create(
            name="C1",
            location="Printer room",
            status=Machine.Status.AVAILABLE,
            machine_type=self.machine_type,
        )
        self.user_with_course_and_quota = User.objects.create_user(
            "User", "user@makentnu.no", "user_pass"
        )
        self.user_quota = Quota.objects.create(
            user=self.user_with_course_and_quota,
            ignore_rules=False,
            number_of_reservations=2,
            machine_type=self.machine_type,
        )
        self.course_registration = Printer3DCourse.objects.create(
            user=self.user_with_course_and_quota,
            username=self.user_with_course_and_quota.username,
            name=self.user_with_course_and_quota.get_full_name(),
            date=datetime.now().date(),
        )
        self.max_time_reservation = 5
        ReservationRule.objects.create(
            machine_type=self.machine_type,
            start_time=parse_time("00:00"),
            days_changed=6,
            end_time=parse_time("23:59"),
            start_days=[Day.MONDAY],
            max_hours=self.max_time_reservation,
            max_inside_border_crossed=self.max_time_reservation,
        )
        self.event = Event.objects.create(title="TEST EVENT")
        self.timeplace = TimePlace.objects.create(
            event=self.event,
            publication_time=timezone.now(),
            start_time=timezone.now() + timedelta(seconds=1),
            end_time=timezone.now() + timedelta(minutes=1),
        )

    def check_reservation_invalid(self, reservation, failed_assertion_message=None):
        self.assertFalse(reservation.validate(), failed_assertion_message)
        try:
            reservation.save()
            self.fail(failed_assertion_message)
        except ValidationError:
            pass

    def check_reservation_valid(self, reservation, failed_assertion_message=None):
        self.assertTrue(reservation.validate(), failed_assertion_message)
        try:
            reservation.save()
        except ValidationError:
            self.fail(failed_assertion_message)

    def create_reservation(
        self,
        relative_start_time: timedelta,
        relative_end_time: timedelta,
        event: Event = None,
        user: User = None,
        machine: Machine = None,
        special=False,
        special_text="",
    ):
        machine = machine or self.machine
        user = user or self.user_with_course_and_quota
        return Reservation(
            user=user,
            machine=machine,
            event=event,
            start_time=timezone.now() + relative_start_time,
            end_time=timezone.now() + relative_end_time,
            special=special,
            special_text=special_text,
        )


class TestReservation(ReservationTestBase):
    def setUp(self):
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        super().init_objs(MachineType.objects.get(pk=1))

        self._original_reservation_future_limit = Reservation.FUTURE_LIMIT

    def tearDown(self):
        Reservation.FUTURE_LIMIT = self._original_reservation_future_limit

    @staticmethod
    def save_past_reservation(reservation):
        validate_function = reservation.validate
        reservation.validate = lambda: True
        reservation.save()
        reservation.validate = validate_function

    def give_user_event_permission(self):
        self.user_with_course_and_quota.add_perms(
            "make_queue.can_create_event_reservation"
        )

    def test_can_create_reservation(self):
        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
            "Reservations should be saveable",
        )

    def test_not_allowed_user_cannot_create_reservation(self):
        self.course_registration.delete()
        self.user_with_course_and_quota.refresh_from_db()
        self.assertFalse(
            self.machine_type.can_user_use(self.user_with_course_and_quota)
        )
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
            "Users who are not allowed to use a machine, should not be able to reserve it",
        )

    def test_reserve_end_time_before_start_time(self):
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(minutes=30)),
            "Reservations should not be able to end before they start",
        )

    def test_reserve_longer_than_maximum_user_time(self):
        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(hours=1), timedelta(hours=self.max_time_reservation + 1.1)
            ),
            "Reservations should not be allowed to exceed the maximum allowed time for the user",
        )

    def test_reserve_in_the_past(self):
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=-1), timedelta(hours=1)),
            "A reservation is invalid if it starts in the past, even though it ends in the future",
        )

        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=-1), timedelta(hours=-0.5)),
            "A reservation is invalid if it is completely in the past",
        )

    def test_make_more_than_one_reservation(self):
        self.user_quota.number_of_reservations = 5
        self.user_quota.save()

        self.assertTrue(
            Quota.can_create_new_reservation(
                self.user_with_course_and_quota, self.machine_type
            )
        )

        for reservation_number in range(5):
            self.check_reservation_valid(
                self.create_reservation(
                    timedelta(days=reservation_number, hours=1),
                    timedelta(days=reservation_number, hours=2),
                ),
                "User should be able to make as many reservations as allowed",
            )

        self.assertFalse(
            Quota.can_create_new_reservation(
                self.user_with_course_and_quota, self.machine_type
            )
        )

    def test_make_more_than_allowed_number_of_reservations(self):
        self.user_quota.number_of_reservations = 5
        self.user_quota.save()

        for reservation_number in range(5):
            self.check_reservation_valid(
                self.create_reservation(
                    timedelta(days=reservation_number, hours=1),
                    timedelta(days=reservation_number, hours=2),
                ),
                "User should be able to make as many reservations as allowed",
            )

        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(days=5, hours=1), timedelta(days=5, hours=2)
            ),
            "User should not be able to make more reservations than allowed",
        )

    @patch("django.utils.timezone.now")
    def test_disallow_overlapping_reservations(self, now_mock):
        now_mock.return_value = parse_datetime_localized("2018-03-12 12:00")

        self.user_quota.number_of_reservations = 3
        self.user_quota.save()

        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
            "Saving should be valid",
        )

        # Start before, end inside
        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(minutes=50), timedelta(hours=1, minutes=50)
            ),
            "Reservation should not be able to end inside another",
        )

        # Start inside, end after
        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(hours=1, minutes=10), timedelta(hours=2, minutes=10)
            ),
            "Reservation should not be able to end inside another",
        )

        # Start inside, end inside
        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(hours=1, minutes=10), timedelta(hours=1, minutes=50)
            ),
            "Reservation should not be able to start and end inside another",
        )

        # Start before, end after
        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(minutes=50), timedelta(hours=2, minutes=10)
            ),
            "Reservation should not be able to encapsulate another",
        )

        # End at the start time of other
        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=0), timedelta(hours=1)),
            "A reservation should be allowed to end at the same time another one starts",
        )

        # Start at the end time of other
        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=2), timedelta(hours=3)),
            "A reservation should be allowed to start at the same time another one ends",
        )

    def test_make_event_without_event_permission(self):
        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(hours=1), timedelta(hours=2), event=self.timeplace
            ),
            "Should not be able to make event reservation without correct permission",
        )

    def test_make_event_with_event_permission(self):
        self.give_user_event_permission()
        self.user_quota.max_number_of_reservations = 1
        self.user_quota.save()

        self.check_reservation_valid(
            self.create_reservation(
                timedelta(hours=1), timedelta(hours=2), event=self.timeplace
            ),
            "User with the correct permission should be allowed to create an event reservation",
        )

        self.check_reservation_valid(
            self.create_reservation(
                timedelta(days=1, hours=1),
                timedelta(days=1, hours=2),
                event=self.timeplace,
            ),
            "Event reservations should not count towards the total number of reservations",
        )

    def test_make_event_reservation_with_longer_than_user_max_time(self):
        self.give_user_event_permission()

        self.check_reservation_valid(
            self.create_reservation(
                timedelta(hours=1),
                timedelta(hours=self.max_time_reservation + 2),
                event=self.timeplace,
            ),
            "User should be able to make event reservations longer than their maximum reservation time",
        )

    def test_change_event_while_maximum_booked(self):
        self.user_quota.max_number_of_reservations = 1
        self.user_quota.save()

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))

        self.check_reservation_valid(reservation, "Reservation should be valid")

        reservation.end_time = timezone.now() + timedelta(hours=3)

        self.check_reservation_valid(
            reservation,
            "Changing a reservation with the maximum number of reservations should be valid",
        )

    def test_same_time_separate_machines(self):
        additional_printer = Machine.objects.create(
            name="C2",
            location="Printer room Mackerspace U1",
            status=Machine.Status.AVAILABLE,
            machine_type=self.machine_type,
        )
        Machine.objects.create(
            name="C3",
            location="Printer room Mackerspace U1",
            status=Machine.Status.AVAILABLE,
            machine_type=self.machine_type,
        )

        self.check_reservation_valid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2)),
            "Saving a single reservation should be valid",
        )

        self.check_reservation_valid(
            self.create_reservation(
                timedelta(hours=1), timedelta(hours=2), machine=additional_printer
            ),
            "Reservations on different printers should be able to overlap in time",
        )

    def test_can_owner_change_future_reservation(self):
        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))
        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )

    def test_can_owner_change_started_reservation(self):
        reservation = self.create_reservation(timedelta(hours=-1), timedelta(hours=2))
        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        self.assertFalse(reservation.can_change_start_time())
        self.assertTrue(reservation.can_change_end_time())

    def test_can_owner_change_end_time_of_started_reservation(self):
        reservation = self.create_reservation(timedelta(hours=-2), timedelta(hours=2))
        self.save_past_reservation(reservation)
        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        reservation.end_time = timezone.now() + timedelta(hours=1)
        self.check_reservation_valid(
            reservation, "Should be able to change end time of started reservation"
        )
        reservation.end_time = timezone.now() + timedelta(hours=-1)
        self.check_reservation_invalid(
            reservation,
            "Should not be able to change end time of started reservation to before the current time",
        )

    def test_can_owner_change_end_time_of_ended_reservation(self):
        reservation = self.create_reservation(timedelta(hours=-3), timedelta(hours=-1))
        self.assertFalse(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )

    def test_can_owner_change_started_event_reservation(self):
        self.give_user_event_permission()

        reservation = self.create_reservation(
            timedelta(hours=-1), timedelta(hours=2), event=self.timeplace
        )
        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )

    def test_can_owner_change_started_special_reservation(self):
        self.give_user_event_permission()

        reservation = self.create_reservation(
            timedelta(hours=-1), timedelta(hours=2), special=True, special_text="Test"
        )
        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )

    def test_can_other_user_change_future_reservation(self):
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))

        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        self.assertFalse(can_change_reservation(reservation, user2))

    def test_can_user_with_event_reservation_change_other_user_non_event_reservation(
        self,
    ):
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        user2.add_perms("make_queue.can_create_event_reservation")

        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))

        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        self.assertFalse(can_change_reservation(reservation, user2))

    def test_can_user_with_event_reservation_change_other_user_event_reservation(self):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        user2.add_perms("make_queue.can_create_event_reservation")

        reservation = self.create_reservation(
            timedelta(hours=1), timedelta(hours=2), event=self.timeplace
        )

        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        self.assertTrue(can_change_reservation(reservation, user2))

    def test_can_user_with_event_reservation_change_other_user_special_reservation(
        self,
    ):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        user2.add_perms("make_queue.can_create_event_reservation")

        reservation = self.create_reservation(
            timedelta(hours=1), timedelta(hours=2), special=True, special_text="Test"
        )

        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        self.assertTrue(can_change_reservation(reservation, user2))

    def test_can_user_without_event_reservation_change_other_user_special_reservation(
        self,
    ):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")

        reservation = self.create_reservation(
            timedelta(hours=1), timedelta(hours=2), special=True, special_text="Test"
        )

        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        self.assertFalse(can_change_reservation(reservation, user2))

    def test_can_user_without_event_reservation_change_other_user_event_reservation(
        self,
    ):
        self.give_user_event_permission()
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")

        reservation = self.create_reservation(
            timedelta(hours=1), timedelta(hours=2), event=self.timeplace
        )

        self.assertTrue(
            can_change_reservation(reservation, self.user_with_course_and_quota)
        )
        self.assertFalse(can_change_reservation(reservation, user2))

    def test_can_delete_future_reservation(self):
        self.assertTrue(
            self.create_reservation(
                timedelta(hours=1), timedelta(hours=2)
            ).can_be_deleted_by(self.user_with_course_and_quota)
        )

    def test_cannot_delete_started_reservation(self):
        self.assertFalse(
            self.create_reservation(
                timedelta(hours=-1), timedelta(hours=2)
            ).can_be_deleted_by(self.user_with_course_and_quota)
        )

    def test_is_within_allowed_period_for_reservation(self):
        Reservation.FUTURE_LIMIT = timedelta(days=7)
        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))
        self.assertTrue(reservation.is_within_allowed_period())
        reservation.end_time = timezone.now() + timedelta(days=7, minutes=2)
        self.assertFalse(reservation.is_within_allowed_period())

    def test_create_reservation_too_far_in_the_future(self):
        Reservation.FUTURE_LIMIT = timedelta(days=7)
        self.check_reservation_invalid(
            self.create_reservation(timedelta(days=7), timedelta(days=7, hours=1)),
            "Reservation is too far in the future and should not be valid",
        )

    def test_make_event_reservation_too_far_in_the_future(self):
        Reservation.FUTURE_LIMIT = timedelta(days=7)
        self.give_user_event_permission()
        self.check_reservation_valid(
            self.create_reservation(
                timedelta(days=7), timedelta(days=7, hours=1), event=self.timeplace
            ),
            "Event reservations are always valid no matter how far in the future they are",
        )

    def set_machine_status(self, status: Machine.Status):
        self.machine.status = status
        self.machine.save()

    def test_cannot_create_reservations_for_machines_out_of_order_or_on_maintenance(
        self,
    ):
        reservation = self.create_reservation(timedelta(hours=1), timedelta(hours=2))
        # Invalid when out of order:
        self.set_machine_status(Machine.Status.OUT_OF_ORDER)
        self.check_reservation_invalid(reservation)
        # Invalid when on maintenance:
        self.set_machine_status(Machine.Status.MAINTENANCE)
        self.check_reservation_invalid(reservation)
        # Valid when available:
        self.set_machine_status(Machine.Status.AVAILABLE)
        self.check_reservation_valid(reservation)

    @patch("django.utils.timezone.now")
    def test_can_make_existing_reservations_shorter_for_machine_out_of_order_or_on_maintenance(
        self, now_mock
    ):
        # Freeze the return value of `timezone.now()`
        now_mock.return_value = parse_datetime_localized("2023-03-06 18:00")

        self.set_machine_status(Machine.Status.AVAILABLE)
        reservation1 = self.create_reservation(timedelta(hours=1), timedelta(hours=5))
        self.check_reservation_valid(reservation1)  # This also saves it

        initial_start_time = reservation1.start_time
        initial_end_time = reservation1.end_time
        for machine_status in (Machine.Status.OUT_OF_ORDER, Machine.Status.MAINTENANCE):
            with self.subTest(machine_status=machine_status):
                self.set_machine_status(machine_status)

                # Making the reservation longer is invalid:
                reservation1.start_time -= timedelta(hours=0.5)
                self.check_reservation_invalid(reservation1)
                reservation1.end_time += timedelta(hours=0.5)
                self.check_reservation_invalid(reservation1)
                reservation1.start_time = initial_start_time
                self.check_reservation_invalid(reservation1)
                reservation1.end_time = initial_end_time

                # Making the reservation shorter is valid:
                reservation1.start_time = initial_start_time + timedelta(hours=0.5)
                self.check_reservation_valid(reservation1)
                reservation1.end_time = initial_end_time - timedelta(hours=0.5)
                self.check_reservation_valid(reservation1)
                reservation1.start_time = initial_start_time + timedelta(hours=1)
                reservation1.end_time = initial_end_time - timedelta(hours=1)
                self.check_reservation_valid(reservation1)

                # Making the reservation longer is valid if the machine is available:
                self.set_machine_status(Machine.Status.AVAILABLE)
                reservation1.start_time -= timedelta(hours=0.5)
                self.check_reservation_valid(reservation1)
                reservation1.end_time += timedelta(hours=0.5)
                self.check_reservation_valid(reservation1)
                # Make it even longer (than it was above) and reset it for the next loop iteration
                reservation1.start_time = initial_start_time
                reservation1.end_time = initial_end_time
                self.check_reservation_valid(reservation1)

        # Skip forward a day and create a new reservation
        now_mock.return_value += timedelta(days=1)
        self.set_machine_status(Machine.Status.AVAILABLE)
        reservation2 = self.create_reservation(timedelta(hours=1), timedelta(hours=5))
        self.check_reservation_valid(reservation2)  # This also saves it
        # Changing the reservation duration after the reservation has started should produce the same results
        now_mock.return_value += timedelta(hours=2)

        initial_end_time = reservation2.end_time
        for machine_status in (Machine.Status.OUT_OF_ORDER, Machine.Status.MAINTENANCE):
            with self.subTest(machine_status=machine_status):
                self.set_machine_status(machine_status)

                # Making the reservation longer is invalid:
                reservation2.end_time += timedelta(hours=0.5)
                self.check_reservation_invalid(reservation2)

                # Making the reservation shorter is valid:
                reservation2.end_time = initial_end_time - timedelta(hours=1)
                self.check_reservation_valid(reservation2)

                # Making the reservation longer is valid if the machine is available:
                self.set_machine_status(Machine.Status.AVAILABLE)
                reservation2.end_time += timedelta(hours=0.5)
                self.check_reservation_valid(reservation2)
                # Make it even longer (than it was above) and reset it for the next loop iteration
                reservation2.end_time = initial_end_time
                self.check_reservation_valid(reservation2)


class TestReservationOfAdvancedPrinters(ReservationTestBase):
    def test_raise3d_printer_can_only_be_reserved_by_users_with_raise3d_course(self):
        def set_raise3d_course(course: Printer3DCourse):
            course.course_permissions.add(
                CoursePermission.objects.get(
                    short_name=CoursePermission.DefaultPerms.TAKEN_RAISE3D_COURSE
                )
            )
            course.save()

        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self._test_advanced_printer_can_only_be_reserved_by_users_with_advanced_course(
            MachineType.objects.get(pk=6), set_raise3d_course
        )

    def test_sla_printer_can_only_be_reserved_by_users_with_sla_course(self):
        def set_sla_course(course: Printer3DCourse):
            course.course_permissions.add(
                CoursePermission.objects.get(
                    short_name=CoursePermission.DefaultPerms.SLA_PRINTER_COURSE
                )
            )
            course.save()

        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self._test_advanced_printer_can_only_be_reserved_by_users_with_advanced_course(
            MachineType.objects.get(pk=7), set_sla_course
        )

    def _test_advanced_printer_can_only_be_reserved_by_users_with_advanced_course(
        self,
        machine_type: MachineType,
        set_advanced_course_func: Callable[[Printer3DCourse], None],
    ):
        super().init_objs(machine_type)

        # User without a course should not be allowed
        user2 = User.objects.create_user("test", "user2@makentnu.no", "test_pass")
        self.check_reservation_invalid(
            self.create_reservation(timedelta(hours=1), timedelta(hours=2), user=user2)
        )

        # User with a normal course should also not be allowed
        self.check_reservation_invalid(
            self.create_reservation(
                timedelta(hours=1),
                timedelta(hours=2),
                user=self.user_with_course_and_quota,
            )
        )

        # User with the advanced course should be allowed
        set_advanced_course_func(self.course_registration)
        self.check_reservation_valid(
            self.create_reservation(
                timedelta(hours=1),
                timedelta(hours=2),
                user=self.user_with_course_and_quota,
            )
        )
