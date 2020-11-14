from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from news.models import Event, TimePlace
from ...forms import BaseMachineForm, EditMachineForm
from ...models.models import Machine, MachineType

class MachineFormTest(TestCase):

    def setUp(self):
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.valid_form_data = {
            "name": "Machine_test1",
            "status": "F",
            "stream_name": "make-0101",
            "location": "Here",
            "location_url": "https://makentnu.no/",
            "machine_model": "multimaker",
            "machine_type": self.printer_machine_type,
        }

    def test_valid_machine_form(self):
        form = BaseMachineForm(data=self.valid_form_data)

        self.assertTrue(form.is_valid())

    def test_stream_name_with_space_returns_false(self):
        form_data = self.valid_form_data
        form_data["stream_name"] = "invalid form"

        form = BaseMachineForm(data=form_data)

        self.assertFalse(form.is_valid())

    def test_stream_name_with_special_character_returns_false(self):
        form_data = self.valid_form_data
        form_data["stream_name"] = "schrödinger"

        form = BaseMachineForm(data=form_data)

        self.assertFalse(form.is_valid())

    def test_empty_stream_name_when_3dprinter_returns_false(self):
        form_data = self.valid_form_data
        form_data["machine_type"] = self.printer_machine_type
        form_data["stream_name"] = ""

        form = BaseMachineForm(data=form_data)

        self.assertFalse(form.is_valid())
    
    def test_empty_stream_name_when_not_3dprinter_returns_true(self):
        form_data = self.valid_form_data
        form_data["machine_type"] = MachineType.objects.get(pk=2)
        form_data["stream_name"] = ""

        form = BaseMachineForm(data=form_data)

        self.assertTrue(form.is_valid())

class EditMachineFormTest(TestCase):

    def setUp(self):
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.machine = Machine.objects.create(name="Test", machine_model="Ultimaker 2+", machine_type=self.printer_machine_type)
        self.valid_form_data = {
            "name": "Machine_test1",
            "status": "F",
            "stream_name": "make-0101",
            "location": "Here",
            "location_url": "https://makentnu.no/",
            "machine_model": "multimaker",
        }

    def test_valid_machine_form(self):
        form = EditMachineForm(data=self.valid_form_data)
        
        self.assertTrue(form.is_valid())

    def test_empty_stream_name_when_3dprinter_returns_false(self):
        form_data = self.valid_form_data
        form_data["stream_name"] = ""

        form = BaseMachineForm(data=form_data)

        self.assertFalse(form.is_valid())

    # Not implemented yet
    # def test_empty_stream_name_when_not_3dprinter_returns_true(self):
    #     form_data = self.valid_form_data
    #     self.machine.machine_type = MachineType.objects.get(pk=2)
    #     form_data["stream_name"] = ""
    #
    #     form = BaseMachineForm(data=form_data)

        self.assertTrue(form.is_valid())