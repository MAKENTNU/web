from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.utils import timezone

from users.models import User
from ...models.course import CoursePermission, Printer3DCourse
from ...models.machine import Machine, MachineType
from ...models.reservation import Quota, Reservation


class TestGenericMachine(TestCase):
    def test_status(self):
        user = User.objects.create_user("test")

        permissions = CoursePermission.objects.all()

        Printer3DCourse.objects.create(
            name="Test", username="test", user=user, date=timezone.localdate()
        )
        Printer3DCourse.objects.get(name="Test").course_permissions.set(permissions)

        self.assertGreaterEqual(MachineType.objects.count(), 1)
        for machine_type in MachineType.objects.all():
            with self.subTest(machine_type=machine_type):
                machine = Machine.objects.create(
                    name=f"{machine_type.name} 1",
                    location="Makerverkstedet",
                    machine_model="Generic machine",
                    machine_type=machine_type,
                )
                Quota.objects.create(
                    machine_type=machine_type,
                    user=user,
                    ignore_rules=True,
                    number_of_reservations=1,
                )

                for set_status, expected_status in {
                    Machine.Status.AVAILABLE: Machine.Status.AVAILABLE,
                    Machine.Status.OUT_OF_ORDER: Machine.Status.OUT_OF_ORDER,
                    Machine.Status.MAINTENANCE: Machine.Status.MAINTENANCE,
                    Machine.Status.RESERVED: Machine.Status.AVAILABLE,
                }.items():
                    self.assert_status_is_as_expected_after_being_set(
                        machine, set_status, expected_status
                    )

                Reservation.objects.create(
                    machine=machine,
                    start_time=timezone.localtime(),
                    end_time=timezone.localtime() + timedelta(hours=1),
                    user=user,
                )

                for set_status, expected_status in {
                    Machine.Status.RESERVED: Machine.Status.RESERVED,
                    Machine.Status.AVAILABLE: Machine.Status.RESERVED,
                    Machine.Status.OUT_OF_ORDER: Machine.Status.OUT_OF_ORDER,
                    Machine.Status.MAINTENANCE: Machine.Status.MAINTENANCE,
                }.items():
                    self.assert_status_is_as_expected_after_being_set(
                        machine, set_status, expected_status
                    )

    def assert_status_is_as_expected_after_being_set(
        self,
        machine: Machine,
        set_status: Machine.Status,
        expexted_status: Machine.Status,
    ):
        machine.status = set_status
        self.assertEqual(machine.get_status(), expexted_status)
        self.assertEqual(
            machine.get_status_display(), Machine.STATUS_CHOICES_DICT[expexted_status]
        )


class TestCanUse3DPrinter(TestCase):
    def setUp(self):
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.machine_type = MachineType.objects.get(pk=1)

    def test_can_user_3d_printer_not_authenticated(self):
        self.assertFalse(MachineType.can_use_3d_printer(AnonymousUser()))

    def test_registered_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(
            user=user,
            username=user.username,
            name=user.get_full_name(),
            date=timezone.now().date(),
        )
        self.assertTrue(MachineType.can_use_3d_printer(user))

    def test_registered_username_for_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(
            username=user.username,
            name=user.get_full_name(),
            date=timezone.now().date(),
        )
        self.assertTrue(MachineType.can_use_3d_printer(user))

    def test_unregistered_user_use_3d_printer(self):
        user = User.objects.create_user("test")
        self.assertFalse(MachineType.can_use_3d_printer(user))
