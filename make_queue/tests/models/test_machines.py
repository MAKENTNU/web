from django.test import TestCase

from make_queue.models import Printer3D, SewingMachine, Machine


class TestGenericMachine(TestCase):

    def test_get_subclass(self):
        self.assertEquals(Machine.get_subclass(Printer3D.literal), Printer3D)
        self.assertEquals(Machine.get_subclass(SewingMachine.literal), SewingMachine)
        try:
            Machine.get_subclass("")
            self.fail("Getting a subclass that does not exist, should throw a StopIteration exception")
        except StopIteration:
            pass


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
