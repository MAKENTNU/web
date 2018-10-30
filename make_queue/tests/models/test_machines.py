from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from make_queue.fields import MachineTypeField
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, Quota, Reservation


class TestGenericMachine(TestCase):

    def test_status(self):
        machine_type = MachineTypeField.get_machine_type(1)
        printer = Machine.objects.create(name="C1", location="Printer room", status="F",
                                         machine_model="Ultimaker 2 Extended", machine_type=machine_type)
        user = User.objects.create_user("test")
        Printer3DCourse.objects.create(name="Test", username="test", user=user, date=timezone.datetime.now().date())
        Quota.objects.create(machine_type=machine_type, user=user, ignore_rules=True, number_of_reservations=1)

        self.assertEquals(printer.get_status(), "F")
        self.assertEquals(printer.get_status_display(), "Ledig")
        printer.status = "O"
        self.assertEquals(printer.get_status(), "O")
        self.assertEquals(printer.get_status_display(), "I ustand")
        printer.status = "M"
        self.assertEquals(printer.get_status(), "M")
        self.assertEquals(printer.get_status_display(), "Vedlikehold")
        printer.status = "R"
        self.assertEquals(printer.get_status(), "F")
        self.assertEquals(printer.get_status_display(), "Ledig")

        Reservation.objects.create(machine=printer, start_time=timezone.now(),
                                   end_time=timezone.now() + timedelta(hours=1), user=user)

        self.assertEquals(printer.get_status(), "R")
        self.assertEquals(printer.get_status_display(), "Reservert")
        printer.status = "F"
        self.assertEquals(printer.get_status(), "R")
        self.assertEquals(printer.get_status_display(), "Reservert")
        printer.status = "O"
        self.assertEquals(printer.get_status(), "O")
        self.assertEquals(printer.get_status_display(), "I ustand")
        printer.status = "M"
        self.assertEquals(printer.get_status(), "M")
        self.assertEquals(printer.get_status_display(), "Vedlikehold")
