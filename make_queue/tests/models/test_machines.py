from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from users.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from make_queue.fields import MachineTypeField, can_use_3d_printer
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, Quota, Reservation


class TestGenericMachine(TestCase):

    def test_status(self):
        machine_type = MachineTypeField.get_machine_type(1)
        printer = Machine.objects.create(name="C1", location="Printer room", machine_model="Ultimaker 2 Extended",
                                         machine_type=machine_type)
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(name="Test", username="test", user=user, date=timezone.datetime.now().date())
        Quota.objects.create(machine_type=machine_type, user=user, ignore_rules=True, number_of_reservations=1)

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
        self.assertEquals(machine.status, status)
        self.assertEquals(machine._get_status_display(), Machine.STATUS_CHOICES_DICT[status])


class TestCanUse3DPrinter(TestCase):

    def setUp(self):
        self.machine_type = MachineTypeField.get_machine_type(1)

    def test_can_user_3d_printer_not_authenticated(self):
        self.assertFalse(can_use_3d_printer(AnonymousUser()))

    def test_registered_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(user=user, username=user.username, name=user.get_full_name(),
                                       date=timezone.now().date())
        self.assertTrue(can_use_3d_printer(user))

    def test_registered_username_for_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(username=user.username, name=user.get_full_name(), date=timezone.now().date())
        self.assertTrue(can_use_3d_printer(user))

    def test_unregistered_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        self.assertFalse(can_use_3d_printer(user))


class TestGetMachineType(TestCase):

    def test_get_machine_type(self):
        for machine_type in MachineTypeField.possible_machine_types:
            self.assertEqual(machine_type, MachineTypeField.get_machine_type(machine_type.id))

        self.assertEqual(None, MachineTypeField.get_machine_type(0))


class TestMachineTypeField(TestCase):

    def test_to_python(self):
        machine_type_field = MachineTypeField()
        self.assertEqual(None, machine_type_field.to_python(None))
        for machine_type in MachineTypeField.possible_machine_types:
            self.assertEqual(machine_type, machine_type_field.to_python(machine_type.id))
            self.assertEqual(machine_type, machine_type_field.to_python(machine_type.id))

        try:
            machine_type_field.to_python(0)
            self.fail("Invalid IDs should fail when converting to python")
        except ValidationError:
            pass

        try:
            machine_type_field.to_python(machine_type_field)
            self.fail("Invalid types should fail when converting to python")
        except ValidationError:
            pass

    def test_get_prep_value(self):
        machine_type_field = MachineTypeField()
        self.assertEqual(None, machine_type_field.get_prep_value(None))
        for machine_type in MachineTypeField.possible_machine_types:
            self.assertEqual(machine_type.id, machine_type_field.get_prep_value(machine_type))
            self.assertEqual(machine_type.id, machine_type_field.get_prep_value([machine_type]))
