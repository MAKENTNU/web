from django.test import TestCase

from make_queue.fields import MachineTypeField
from make_queue.models.models import Machine
from make_queue.tests.utility import template_view_get_context_data
from make_queue.views.reservation.machine import MachineView


class MachineViewTest(TestCase):
    def test_no_machines(self):
        self.assertEqual(template_view_get_context_data(MachineView), {"machine_types": []})

    def test_one_type_of_machine(self):
        machine_type_printer = MachineTypeField.get_machine_type(1)
        printer1 = Machine.objects.create(name="test1", machine_type=machine_type_printer)
        printer2 = Machine.objects.create(name="test2", machine_type=machine_type_printer)
        self.assertEqual(template_view_get_context_data(MachineView), {"machine_types": [{
            "name": machine_type_printer.name,
            "type": machine_type_printer,
            "machines": [printer1, printer2],
        }]})

    def test_several_machine_types(self):
        machine_type_printer = MachineTypeField.get_machine_type(1)
        machine_type_sewing = MachineTypeField.get_machine_type(2)
        printer1 = Machine.objects.create(name="test1", machine_type=machine_type_printer)
        printer2 = Machine.objects.create(name="test2", machine_type=machine_type_printer)
        sewing = Machine.objects.create(name="test", machine_type=machine_type_sewing)
        self.assertEqual(template_view_get_context_data(MachineView), {"machine_types": [{
            "name": machine_type_printer.name,
            "type": machine_type_printer,
            "machines": [printer1, printer2],
        }, {
            "name": machine_type_sewing.name,
            "type": machine_type_sewing,
            "machines": [sewing],
        }]})
