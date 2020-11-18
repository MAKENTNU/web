from typing import Union

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from users.models import User
from ...models.models import Machine, MachineType
from ...tests.utility import template_view_get_context_data
from ...views.reservation.machine import MachineView
from ...forms import EditMachineForm, BaseMachineForm


class MachineViewTest(TestCase):

    def test_no_machines(self):
        context_data = template_view_get_context_data(MachineView)
        self.assertIn("machine_types", context_data)
        self.assertFalse(context_data["machine_types"].exists())

    def test_one_type_of_machine(self):
        printer_machine_type = MachineType.objects.get(pk=1)
        printer1 = Machine.objects.create(name="test1", machine_type=printer_machine_type)
        printer2 = Machine.objects.create(name="test2", machine_type=printer_machine_type)

        machine_types = list(template_view_get_context_data(MachineView)["machine_types"])
        self.assertEqual(len(machine_types), 1)
        machine_type_0 = machine_types[0]
        self.assertEqual(machine_type_0.pk, printer_machine_type.pk)
        self.assertEqual(machine_type_0.name, printer_machine_type.name)
        self.assertListEqual(list(machine_type_0.existing_machines), [printer1, printer2])

    def test_several_machine_types(self):
        printer_machine_type = MachineType.objects.get(pk=1)
        sewing_machine_type = MachineType.objects.get(pk=2)
        printer1 = Machine.objects.create(name="test1", machine_type=printer_machine_type)
        printer2 = Machine.objects.create(name="test2", machine_type=printer_machine_type)
        sewing = Machine.objects.create(name="test", machine_type=sewing_machine_type)

        machine_types = list(template_view_get_context_data(MachineView)["machine_types"])
        self.assertEqual(len(machine_types), 2)
        machine_type_0, machine_type_1 = machine_types
        self.assertEqual(machine_type_0.pk, printer_machine_type.pk)
        self.assertEqual(machine_type_1.pk, sewing_machine_type.pk)
        self.assertEqual(machine_type_0.name, printer_machine_type.name)
        self.assertEqual(machine_type_1.name, sewing_machine_type.name)
        self.assertListEqual(list(machine_type_0.existing_machines), [printer1, printer2])
        self.assertListEqual(list(machine_type_1.existing_machines), [sewing])

    def test_machines_are_sorted_correctly(self):
        def create_machine(name_prefix: str, machine_type_: MachineType, priority: Union[int, None]):
            return Machine.objects.create(
                name=f"{name_prefix} {machine_type_.name}",
                machine_type=machine_type_,
                priority=priority,
            )

        printer_machine_type = MachineType.objects.get(pk=1)
        sewing_machine_type = MachineType.objects.get(pk=2)
        correct_machine_orders = []
        for machine_type in (printer_machine_type, sewing_machine_type):
            machine_b = create_machine("b", machine_type, None)
            machine_c = create_machine("c", machine_type, None)
            machine_d = create_machine("d", machine_type, None)
            machine_1_h = create_machine("h", machine_type, 1)
            machine_3_e = create_machine("e", machine_type, 3)
            machine_2_f = create_machine("f", machine_type, 2)
            machine_2_g = create_machine("g", machine_type, 2)
            machine_2_a = create_machine("a", machine_type, 2)
            correct_machine_orders.append([
                machine_1_h,
                machine_2_a, machine_2_f, machine_2_g,
                machine_3_e,
                machine_b, machine_c, machine_d,
            ])

        machine_types = list(template_view_get_context_data(MachineView)["machine_types"])
        for machine_type, correct_machine_order in zip(machine_types, correct_machine_orders):
            with self.subTest(machine_type=machine_type):
                self.assertListEqual(list(machine_type.existing_machines), correct_machine_order)

class CreateAndEditMachineViewTest(TestCase):

    def setUp(self):
        username = 'TEST_USER'
        password = 'TEST_PASS'
        self.user = User.objects.create_user(username=username, password=password)
        change_permission = Permission.objects.get(codename="change_machine")
        create_permission = Permission.objects.get(codename="add_machine")
        self.user.user_permissions.add(create_permission, change_permission)
        self.client.login(username=username, password=password)

    def test_editMachine_context_data_has_EditMachineForm(self):
        printer_machine_type = MachineType.objects.get(pk=1)
        machine = Machine.objects.create(
            name="Test",
            machine_model="Ultimaker 2+",
            machine_type=printer_machine_type
        )
        self.response = self.client.get(reverse("edit_machine", args=[machine.pk]))
        
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(isinstance(self.response.context_data["form"], EditMachineForm))

    def test_createMachine_context_data_has_baseMachineForm(self):
        self.response = self.client.get(reverse("create_machine"))
        
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(isinstance(self.response.context_data["form"], BaseMachineForm))
