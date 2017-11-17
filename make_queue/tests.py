from django.test import TestCase
from make_queue.models import Printer3D, Reservation3D, Quota3D
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class Reservation3DTestCase(TestCase):
    def setUp(self):
        Printer3D.objects.create(name="C1", location="Printer room Makerspace U1", status="F")
        user = User.objects.create_user("User", "user@makentnu.no", "user_pass")
        user.save()
        Quota3D.objects.create(user=user, can_print=True, max_time_reservation=10, max_number_of_reservations=2)

    def test_can_create_reservation(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=2),
                                    event=False)

        self.assertTrue(reservation.validate())
        try:
            reservation.save()
        except ValidationError:
            self.fail("Could not save a valid reservation")

    def test_user_that_cannot_print_cannot_reserve(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")
        user_quota = user.quota3d
        user_quota.can_print = False
        user_quota.save()

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=2),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Saving an invalid reservation should throw a ValidationError")
        except ValidationError:
            pass

    def test_reserve_longer_than_maximum_user_time(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(),
                                    end_time=timezone.now() + timedelta(hours=user.quota3d.max_time_reservation + 0.1),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Saving a reservation longer than the maximum allowed time for that user")
        except ValidationError:
            pass

    def test_reserve_end_time_before_start_time(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(), end_time=timezone.now() - timedelta(hours=1),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Saving a reservation with end time before start time should fail")
        except ValidationError:
            pass

    def test_make_more_than_one_reservation(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")
        quota = user.quota3d
        quota.max_number_of_reservations = 5
        quota.save()

        for reservation_number in range(user.quota3d.max_number_of_reservations):
            reservation = Reservation3D(user=user, printer=printer,
                                        start_time=timezone.now() + timedelta(days=reservation_number),
                                        end_time=timezone.now() + timedelta(days=reservation_number, hours=2),
                                        event=False)

            self.assertTrue(reservation.validate())
            try:
                reservation.save()
            except ValidationError:
                self.fail("Saving should be valid")

    def test_make_more_than_allowed_number_of_reservations(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        for reservation_number in range(user.quota3d.max_number_of_reservations):
            reservation = Reservation3D(user=user, printer=printer,
                                        start_time=timezone.now() + timedelta(days=reservation_number),
                                        end_time=timezone.now() + timedelta(days=reservation_number, hours=2),
                                        event=False)

            self.assertTrue(reservation.validate())
            try:
                reservation.save()
            except ValidationError:
                self.fail("Saving should be valid")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now() + timedelta(days=user.quota3d.max_number_of_reservations),
                                    end_time=timezone.now() + timedelta(days=user.quota3d.max_number_of_reservations,
                                                                        hours=2))

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("User should not be able to make more reservations than allowed")
        except ValidationError:
            pass

    def test_disallow_overlapping_reservations(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        start_time_base = timezone.now()

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=start_time_base, end_time=start_time_base + timedelta(hours=1),
                                    event=False)

        self.assertTrue(reservation.validate())
        try:
            reservation.save()
        except ValidationError:
            self.fail("Saving should be valid")

        # Start before, end inside
        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=start_time_base - timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(minutes=50),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Reservation should not be able to end inside another")
        except ValidationError:
            pass

        # Start inside, end after
        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=start_time_base + timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(hours=1, minutes=10),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Reservation should not be able to end inside another")
        except ValidationError:
            pass

        # Start inside, end inside
        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=start_time_base + timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(minutes=50),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Reservation should not be able to start and end inside another")
        except ValidationError:
            pass

        # Start before, end after
        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=start_time_base - timedelta(minutes=10),
                                    end_time=start_time_base + timedelta(hours=1, minutes=10),
                                    event=False)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Reservation should not be able to encapsulate another")
        except ValidationError:
            pass

    def test_make_event_without_event_permission(self):
        printer = Printer3D.objects.get(name="C1")
        user = User.objects.get(username="User")

        reservation = Reservation3D(user=user, printer=printer,
                                    start_time=timezone.now(), end_time=timezone.now() + timedelta(hours=2),
                                    event=True)

        self.assertFalse(reservation.validate())
        try:
            reservation.save()
            self.fail("Should not be able to make event reservation without correct permission")
        except ValidationError:
            pass
