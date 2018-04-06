from django.test import TestCase

from make_queue.models import Printer3D, SewingMachine
from make_queue.tests.utility import template_view_get_context_data
from make_queue.views.reservation.machine import MachineView


class MachineViewTest(TestCase):

    def test_no_machines(self):
        self.assertEqual(template_view_get_context_data(MachineView), {"machine_types": []})

    def test_one_type_of_machine(self):
        printer1 = Printer3D.objects.create(name="test1")
        printer2 = Printer3D.objects.create(name="test2")
        self.assertEqual(template_view_get_context_data(MachineView), {"machine_types": [{
            "name": Printer3D.literal,
            "machines": [printer1, printer2]
        }]})

    def test_several_machine_types(self):
        printer1 = Printer3D.objects.create(name="test1")
        printer2 = Printer3D.objects.create(name="test2")
        sewing = SewingMachine.objects.create(name="test")
        self.assertEqual(template_view_get_context_data(MachineView), {"machine_types": [{
            "name": Printer3D.literal,
            "machines": [printer1, printer2],
        }, {
            "name": SewingMachine.literal,
            "machines": [sewing],
        }]})
