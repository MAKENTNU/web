from django.test import TestCase
from django.utils import timezone

from users.models import User
from ..utility import template_view_get_context_data
from ...models.course import Printer3DCourse
from ...models.models import Machine, MachineType, Quota, Reservation
from ...views.reservation.overview import MyReservationsView


class MyReservationsViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("user", "user@makentnu.no")

        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.printer_machine_type = MachineType.objects.get(pk=1)

        printer = Machine.objects.create(name="U1", machine_type=self.printer_machine_type,
                                         machine_model="Ultimaker 2", location="S1", status=Machine.Status.AVAILABLE)
        Quota.objects.create(user=self.user, number_of_reservations=2, ignore_rules=True,
                             machine_type=self.printer_machine_type)
        Printer3DCourse.objects.create(user=self.user, name=self.user.get_full_name(), username=self.user.username,
                                       date=timezone.now().date())

        Reservation.objects.create(user=self.user, machine=printer, event=None,
                                   start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=2))

    def test_get_user_reservations_single_reservation(self):
        self.assertListEqual(
            [Reservation.objects.get(user=self.user)],
            list(template_view_get_context_data(MyReservationsView, request_user=self.user)["reservations"])
        )

    def test_get_user_reservations_multiple_reservations(self):
        Reservation.objects.create(user=self.user,
                                   machine=Machine.objects.get(name="U1"),
                                   start_time=timezone.now() + timezone.timedelta(hours=2),
                                   end_time=timezone.now() + timezone.timedelta(hours=4), event=None)

        self.assertListEqual(
            list(self.user.reservations.order_by("-start_time")),
            list(template_view_get_context_data(MyReservationsView, request_user=self.user)["reservations"])
        )

    def test_get_user_reservations_different_types(self):
        sewing_machine_type = MachineType.objects.get(pk=2)
        Quota.objects.create(user=self.user, number_of_reservations=2, machine_type=sewing_machine_type,
                             ignore_rules=True)

        sewing_machine = Machine.objects.create(name="T1", machine_model="Generic", location="M1", status=Machine.Status.AVAILABLE,
                                                machine_type=sewing_machine_type)

        Reservation.objects.create(user=self.user, machine=sewing_machine,
                                   start_time=timezone.now(),
                                   end_time=timezone.now() + timezone.timedelta(hours=2), event=None)

        self.assertListEqual(
            [
                Reservation.objects.get(user=self.user, machine__machine_type=sewing_machine_type),
                Reservation.objects.get(user=self.user, machine__machine_type=self.printer_machine_type),
            ],
            list(template_view_get_context_data(MyReservationsView, request_user=self.user)["reservations"])
        )
