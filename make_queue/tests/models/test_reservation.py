from django.test import TestCase
from make_queue.models import Printer3D, Reservation3D, Quota3D, QuotaSewing, SewingMachine, ReservationSewing
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from news.models import Event


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
        Event.objects.create(title="TEST EVENT",
                             pub_date=timezone.now(),
                             start_date=timezone.now(),
                             start_time=(timezone.now() + timedelta(seconds=1)).time())
        Printer3D.objects.create(name="C1", location="Printer room", status="F")
        user = User.objects.create_user("User", "user@makentnu.no", "user_pass")
        user.save()
        Quota3D.objects.create(user=user, can_print=True, max_time_reservation=10, max_number_of_reservations=2)

    def test_can_create_reservation(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=2), event=None)

        self.check_reservation_valid(reservation, "Reservations should be saveable")

    def test_reserve_end_time_before_start_time(self):

        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now(),
                                    end_time=timezone.now() - timedelta(hours=1), event=None)

        self.check_reservation_invalid(reservation, "Reservations should not be able to end before they start")

    def test_reserve_longer_than_maximum_user_time(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=user.quota3d.max_time_reservation + 0.1),
                                    event=None)

        self.check_reservation_invalid(reservation,
                                       "Reservations should not be allowed to exceed the maximum allowed time for the user")

    def test_make_more_than_one_reservation(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")
        quota = user.quota3d
        quota.max_number_of_reservations = 5
        quota.save()

        for reservation_number in range(user.quota3d.max_number_of_reservations):
            reservation = Reservation3D(user=user, machine=printer,
                                        start_time=timezone.now() + timedelta(days=reservation_number),
                                        end_time=timezone.now() + timedelta(days=reservation_number, hours=2),
                                        event=None)

            self.check_reservation_valid(reservation, "User should be able to make as many reservations as allowed")

    def test_make_more_than_allowed_number_of_reservations(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        for reservation_number in range(user.quota3d.max_number_of_reservations):
            reservation = Reservation3D(user=user, machine=printer,
                                        start_time=timezone.now() + timedelta(days=reservation_number),
                                        end_time=timezone.now() + timedelta(days=reservation_number, hours=2),
                                        event=None)

            self.check_reservation_valid(reservation, "User should be able to make as many reservations as allowed")

        reservation = Reservation3D(user=user, machine=printer,
                                    start_time=timezone.now() + timedelta(days=user.quota3d.max_number_of_reservations),
                                    end_time=timezone.now() + timedelta(days=user.quota3d.max_number_of_reservations,
                                                                        hours=2))

        self.check_reservation_invalid(reservation, "User should not be able to make more reservations than allowed")

    def test_disallow_overlapping_reservations(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        start_time_base = timezone.now()

        reservation = Reservation3D(user=user, machine=printer, start_time=start_time_base,
                                    end_time=start_time_base + timedelta(hours=1), event=None)

        self.check_reservation_valid(reservation, "Saving should be valid")

        # Start before, end inside
        reservation = Reservation3D(user=user, machine=printer, start_time=start_time_base - timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(minutes=50), event=None)

        self.check_reservation_invalid(reservation, "Reservation should not be able to end inside another")

        # Start inside, end after
        reservation = Reservation3D(user=user, machine=printer, start_time=start_time_base + timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(hours=1, minutes=10), event=None)

        self.check_reservation_invalid(reservation, "Reservation should not be able to end inside another")

        # Start inside, end inside
        reservation = Reservation3D(user=user, machine=printer, start_time=start_time_base + timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(minutes=50), event=None)

        self.check_reservation_invalid(reservation, "Reservation should not be able to start and end inside another")

        # Start before, end after
        reservation = Reservation3D(user=user, machine=printer, start_time=start_time_base - timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(hours=1, minutes=10), event=None)

        self.check_reservation_invalid(reservation, "Reservation should not be able to encapsulate another")

    def test_make_event_without_event_permission(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=2), event=Event.objects.get(title="TEST EVENT"))

        self.check_reservation_invalid(reservation,
                                       "Should not be able to make event reservation without correct permission")

    def test_make_event_with_event_permission(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")
        event_permission = Permission.objects.get(name="Can create event reservation")

        user.user_permissions.add(event_permission)
        user.quota3d.max_number_of_reservations = 1
        user.save()

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=2), event=Event.objects.get(title="TEST EVENT"))

        self.check_reservation_valid(reservation,
                                     "User with the correct permission should be allowed to create an event reservation")

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now() + timedelta(days=1),
                                    end_time=timezone.now() + timedelta(days=1, hours=2), event=None)

        self.check_reservation_valid(reservation,
                                     "Event reservations should not count towards the total number of reservations")

    def test_make_event_reservation_with_longer_than_user_max_time(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")
        event_permission = Permission.objects.get(name="Can create event reservation")

        user.user_permissions.add(event_permission)
        user.save()

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=user.quota3d.max_time_reservation + 1),
                                    event=Event.objects.get(title="TEST EVENT"))

        self.check_reservation_valid(reservation,
                                     "User should be able to make event reservations longer than their maximum reservation time")

    def test_change_event_while_maximum_booked(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        user.quota3d.max_number_of_reservations = 1
        user.quota3d.save()

        reservation = Reservation3D(user=user, machine=printer, start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=2), event=None)

        self.check_reservation_valid(reservation, "Reservation should be valid")

        reservation.end_time = timezone.now() + timedelta(hours=3)

        self.check_reservation_valid(reservation,
                                     "Changing a reservation with the maximum number of reservations should be valid")

    def test_same_time_separate_machines(self):
        printer1 = Printer3D.objects.get(name="C1")
        printer2 = Printer3D.objects.create(name="C1", location="Printer room Mackerspace U1", status="F")

        user = User.objects.get(username="User")

        reservation1 = Reservation3D(user=user, machine=printer1, start_time=timezone.now(),
                                     end_time=timezone.now() + timedelta(hours=2), event=None)

        self.check_reservation_valid(reservation1, "Saving a single reservation should be valid")

        reservation2 = Reservation3D(user=user, machine=printer2, start_time=timezone.now(),
                                     end_time=timezone.now() + timedelta(hours=2), event=None)

        self.check_reservation_valid(reservation2,
                                     "Reservations on different printers should be able to overlap in time")


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

    def test_to_string(self):
        self.assertEqual(str(SewingMachine.objects.get(name="C1")), "C1-Generic")


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

    def test_to_string(self):
        self.assertEqual(str(Printer3D.objects.get(name="C1")), "C1-Ultimaker 2")
