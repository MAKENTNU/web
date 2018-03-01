from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from make_queue.models import Printer3D, SewingMachine, Machine, Reservation3D, Quota3D


class TestGenericMachine(TestCase):

    def test_get_subclass(self):
        self.assertEquals(Machine.get_subclass(Printer3D.literal), Printer3D)
        self.assertEquals(Machine.get_subclass(SewingMachine.literal), SewingMachine)
        try:
            Machine.get_subclass("")
            self.fail("Getting a subclass that does not exist, should throw a StopIteration exception")
        except StopIteration:
            pass

    def test_status(self):
        printer = Printer3D.objects.create(name="C1", location="Printer room", status="F", model="Ultimaker 2 Extended")
        user = User.objects.create_user("test")
        Quota3D.objects.create(user=user, can_print=True)

        self.assertEquals(printer.get_status(), "F")
        printer.status = "O"
        self.assertEquals(printer.get_status(), "O")
        printer.status = "M"
        self.assertEquals(printer.get_status(), "M")
        printer.status = "R"
        self.assertEquals(printer.get_status(), "F")

        Reservation3D.objects.create(machine=printer, start_time=timezone.now(),
                                     end_time=timezone.now() + timedelta(hours=1), user=user)

        self.assertEquals(printer.get_status(), "R")
        printer.status = "F"
        self.assertEquals(printer.get_status(), "R")
        printer.status = "O"
        self.assertEquals(printer.get_status(), "O")
        printer.status = "M"
        self.assertEquals(printer.get_status(), "M")

    def test_get_status_display(self):
        printer = Printer3D.objects.create(name="C1", location="Printer room", status="F", model="Ultimaker 2 Extended")
        user = User.objects.create_user("test")
        Quota3D.objects.create(user=user, can_print=True)

        self.assertEquals(printer.get_status_display(), "Ledig")
        printer.status = "O"
        self.assertEquals(printer.get_status_display(), "I ustand")
        printer.status = "M"
        self.assertEquals(printer.get_status_display(), "Vedlikehold")
        printer.status = "R"
        self.assertEquals(printer.get_status_display(), "Ledig")

        Reservation3D.objects.create(machine=printer, start_time=timezone.now(),
                                     end_time=timezone.now() + timedelta(hours=1), user=user)

        self.assertEquals(printer.get_status_display(), "Reservert")
        printer.status = "F"
        self.assertEquals(printer.get_status_display(), "Reservert")
        printer.status = "O"
        self.assertEquals(printer.get_status_display(), "I ustand")
        printer.status = "M"
        self.assertEquals(printer.get_status_display(), "Vedlikehold")


class Printer3DTest(TestCase):

    def setUp(self):
        self.printer = Printer3D.objects.create(name="C1", location="Printer room", status="F",
                                                model="Ultimaker 2 Extended")

    def test_to_string(self):
        self.assertEqual(str(self.printer), "C1 - Ultimaker 2 Extended")


class SewingTest(TestCase):

    def setUp(self):
        self.sewing = SewingMachine.objects.create(name="C1", location="Makerspace U1", status="F", model="Generic")

    def test_to_string(self):
        self.assertEqual(str(self.sewing), "C1 - Generic")
