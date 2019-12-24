from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from users.models import User
from django.test import TestCase
from django.utils import timezone

from ...models.course import Printer3DCourse
from ...models.models import Machine, MachineType, Quota, Reservation


class TestGenericMachine(TestCase):

    def test_status(self):
        printer_machine_type = MachineType.objects.get(pk=1)
        printer = Machine.objects.create(name="C1", location="Printer room",
                                         machine_model="Ultimaker 2 Extended", machine_type=printer_machine_type)
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(name="Test", username="test", user=user, date=timezone.datetime.now().date())
        Quota.objects.create(machine_type=printer_machine_type, user=user, ignore_rules=True, number_of_reservations=1)

        self.check_status(printer, Machine.AVAILABLE)
        printer.out_of_order = True
        self.check_status(printer, Machine.OUT_OF_ORDER)
        printer.out_of_order = False
        self.check_status(printer, Machine.AVAILABLE)

        Reservation.objects.create(machine=printer, start_time=timezone.now(),
                                   end_time=timezone.now() + timedelta(hours=1), user=user)

        self.check_status(printer, Machine.RESERVED)
        printer.out_of_order = True
        self.check_status(printer, Machine.OUT_OF_ORDER)

    def check_status(self, machine, status):
        self.assertEquals(machine.get_status(), status)
        self.assertEquals(machine._get_status_display(), Machine.STATUS_CHOICES_DICT[status])


class TestCanUse3DPrinter(TestCase):

    def setUp(self):
        self.machine_type = MachineType.objects.get(pk=1)

    def test_can_user_3d_printer_not_authenticated(self):
        self.assertFalse(MachineType.can_use_3d_printer(AnonymousUser()))

    def test_registered_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(user=user, username=user.username, name=user.get_full_name(),
                                       date=timezone.now().date())
        self.assertTrue(MachineType.can_use_3d_printer(user))

    def test_registered_username_for_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(username=user.username, name=user.get_full_name(), date=timezone.now().date())
        self.assertTrue(MachineType.can_use_3d_printer(user))

    def test_unregistered_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        self.assertFalse(MachineType.can_use_3d_printer(user))
