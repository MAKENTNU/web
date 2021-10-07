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

    def test_stream_name_with_space_returns_error_must_be_slug(self):
        form_data = self.valid_form_data
        form_data["stream_name"] = "invalid form"

        form = BaseMachineForm(data=form_data)

        self.assertErrorCodeInForm(
            field_name='stream_name',
            error_code='not_url_safe',
            form=form
        )

    def test_stream_name_with_special_character_returns_error_must_be_slug(self):
        form_data = self.valid_form_data
        form_data["stream_name"] = "schrödinger"

        form = BaseMachineForm(data=form_data)

        self.assertErrorCodeInForm(
            field_name='stream_name',
            error_code='not_url_safe',
            form=form
        )

    def test_empty_stream_name_when_3dprinter_returns_error_cannot_be_empty(self):
        form_data = self.valid_form_data
        form_data["machine_type"] = self.printer_machine_type
        form_data["stream_name"] = ""

        form = BaseMachineForm(data=form_data)

        self.assertErrorCodeInForm(
            field_name='stream_name',
            error_code='stream_name_is_none',
            form=form
        )

    def test_empty_stream_name_when_not_3dprinter_returns_true_with_no_form_errors(self):
        form_data = self.valid_form_data
        form_data["machine_type"] = MachineType.objects.get(pk=2)
        form_data["stream_name"] = ""

        form = BaseMachineForm(data=form_data)

        self.assertTrue(form.is_valid())
        self.assertDictEqual({}, form.errors)

    def assertErrorCodeInForm(self, field_name, error_code, form):
        """Asserts ``error_code`` appears among the errors for ``field_name`` in ``form``"""
        error_data = form.errors.as_data()
        error_list = error_data.get(field_name)
        self.assertIsNotNone(error_list)
        error_code_list = [err.code for err in error_list]
        self.assertIn(error_code, error_code_list)


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
        form = EditMachineForm(instance=self.machine, data=self.valid_form_data)

        self.assertTrue(form.is_valid())

    def test_empty_stream_name_when_3dprinter_returns_false(self):
        form_data = self.valid_form_data
        form_data["stream_name"] = ""

        form = EditMachineForm(instance=self.machine, data=form_data)

        self.assertFalse(form.is_valid())

    def test_empty_stream_name_when_not_3dprinter_returns_true(self):
        self.machine.machine_type = MachineType.objects.get(pk=2)
        self.machine.save()
        form_data = self.valid_form_data
        form_data["stream_name"] = ""

        form = EditMachineForm(instance=self.machine, data=form_data)

        self.assertTrue(form.is_valid())
