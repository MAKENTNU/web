from django.test import TestCase

from make_queue.models import Printer3D, SewingMachine


class Printer3DTest(TestCase):

    def setUp(self):
        self.printer = Printer3D.objects.create(name="C1", location="Printer room", status="F")

    def test_to_string(self):
        self.assertEqual(str(self.printer), "C1 - Printer room")


class SewingTest(TestCase):

    def setUp(self):
        self.sewing = SewingMachine.objects.create(name="C1", location="Makerspace U1", status="F", model="Generic")

    def test_to_string(self):
        self.assertEqual(str(self.sewing), "C1 - Makerspace U1")
