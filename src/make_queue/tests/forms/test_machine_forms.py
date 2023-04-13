from datetime import datetime
from unittest import mock

from django.test import TestCase

from util.locale_utils import parse_datetime_localized
from util.test_utils import with_time
from ...forms import AddMachineForm, ChangeMachineForm
from ...models.machine import Machine, MachineType


class TestCreateMachineForm(TestCase):

    def setUp(self):
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.valid_form_data = {
            'name': "Machine_test1",
            'status': Machine.Status.AVAILABLE,
            'stream_name': "make-0101",
            'location': "Here",
            'location_url': "https://makentnu.no/",
            'machine_model': "multimaker",
            'machine_type': self.printer_machine_type,
        }

    def test_valid_machine_form(self):
        form = AddMachineForm(data=self.valid_form_data)

        self.assertTrue(form.is_valid())

    def test_stream_name_with_space_returns_error_must_be_slug(self):
        form_data = self.valid_form_data
        form_data['stream_name'] = "invalid form"

        form = AddMachineForm(data=form_data)

        self.assertErrorCodeInForm(
            field_name='stream_name',
            error_code='invalid_lowercase_slug',
            form=form,
        )

    def test_stream_name_with_special_character_returns_error_must_be_slug(self):
        form_data = self.valid_form_data
        form_data['stream_name'] = "schrödinger"

        form = AddMachineForm(data=form_data)

        self.assertErrorCodeInForm(
            field_name='stream_name',
            error_code='invalid_lowercase_slug',
            form=form,
        )

    def test_empty_stream_name_when_3dprinter_returns_error_cannot_be_empty(self):
        form_data = self.valid_form_data
        form_data['machine_type'] = self.printer_machine_type
        form_data['stream_name'] = ""

        form = AddMachineForm(data=form_data)

        self.assertErrorCodeInForm(
            field_name='stream_name',
            error_code='invalid_empty_stream_name',
            form=form,
        )

    def test_empty_stream_name_when_not_3dprinter_returns_true_with_no_form_errors(self):
        form_data = self.valid_form_data
        form_data['machine_type'] = MachineType.objects.get(pk=2)
        form_data['stream_name'] = ""

        form = AddMachineForm(data=form_data)

        self.assertTrue(form.is_valid())
        self.assertDictEqual({}, form.errors)

    @mock.patch('django.utils.timezone.now')
    def test_info_message_date_defaults_to_now(self, now_mock):
        base_datetime = parse_datetime_localized("2022-04-20 00:00")
        now_mock.return_value = base_datetime

        form_data = self.valid_form_data
        # Default info message date should be now
        form = AddMachineForm(data=form_data)
        machine = form.save()
        self.assertEqual(machine.info_message_date, base_datetime)

    @mock.patch('django.utils.timezone.now')
    def test_trying_to_set_info_message_date_is_ignored(self, now_mock):
        base_datetime = parse_datetime_localized("2022-04-20 00:00")
        now_mock.return_value = base_datetime

        form_data = self.valid_form_data
        form_data['info_message_date'] = with_time(base_datetime, "01:00")
        form = AddMachineForm(data=form_data)
        machine = form.save()
        self.assertEqual(machine.info_message_date, with_time(base_datetime, "00:00"))

    def assertErrorCodeInForm(self, field_name, error_code, form):
        """Asserts ``error_code`` appears among the errors for ``field_name`` in ``form``"""
        error_data = form.errors.as_data()
        error_list = error_data.get(field_name)
        self.assertIsNotNone(error_list)
        error_code_list = {err.code for err in error_list}
        self.assertIn(error_code, error_code_list)


class TestEditMachineForm(TestCase):

    def setUp(self):
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.machine = Machine.objects.create(name="Test", machine_model="Ultimaker 2+", machine_type=self.printer_machine_type)
        self.valid_form_data = {
            'name': "Machine_test1",
            'status': Machine.Status.AVAILABLE,
            'stream_name': "make-0101",
            'location': "Here",
            'location_url': "https://makentnu.no/",
            'machine_model': "multimaker",
        }

    def test_valid_machine_form(self):
        form = ChangeMachineForm(instance=self.machine, data=self.valid_form_data)
        self.assertTrue(form.is_valid())

    def test_empty_stream_name_when_3dprinter_returns_false(self):
        form_data = self.valid_form_data
        form_data['stream_name'] = ""

        form = ChangeMachineForm(instance=self.machine, data=form_data)
        self.assertFalse(form.is_valid())

    def test_empty_stream_name_when_not_3dprinter_returns_true(self):
        self.machine.machine_type = MachineType.objects.get(pk=2)
        self.machine.save()
        form_data = self.valid_form_data
        form_data['stream_name'] = ""

        form = ChangeMachineForm(instance=self.machine, data=form_data)
        self.assertTrue(form.is_valid())

    @mock.patch('django.utils.timezone.now')
    def test_info_message_date_is_appropriately_set(self, now_mock):
        base_datetime = parse_datetime_localized("2022-04-20 00:00")
        now_mock.return_value = base_datetime

        # Default info message date should be now
        self.machine = Machine.objects.create(name="Test 2", machine_model="Ultimaker 2+", machine_type=self.printer_machine_type)
        self.assertEqual(self.machine.info_message_date, base_datetime)

        now_mock.return_value = with_time(base_datetime, "01:00")

        form_data = self.valid_form_data

        def assert_editing_machine_makes_info_message_date_equal(datetime_obj: datetime):
            form = ChangeMachineForm(instance=self.machine, data=form_data)
            self.machine = form.save()
            self.assertEqual(self.machine.info_message_date, datetime_obj)

        # Info message date should be updated when info message is changed
        form_data['info_message'] = "Something is wrong :("
        assert_editing_machine_makes_info_message_date_equal(with_time(base_datetime, "01:00"))

        now_mock.return_value = with_time(base_datetime, "02:00")

        # Info message date should remain unchanged when info message is also not changed
        assert_editing_machine_makes_info_message_date_equal(with_time(base_datetime, "01:00"))

        now_mock.return_value = with_time(base_datetime, "03:00")

        # Trying to set info message date through the form should be ignored
        form_data['info_message_date'] = with_time(base_datetime, "03:00")
        assert_editing_machine_makes_info_message_date_equal(with_time(base_datetime, "01:00"))
        del form_data['info_message_date']

        now_mock.return_value = with_time(base_datetime, "04:00")

        # Removing info message from the form data should be interpreted as it having changed (Django default),
        # and so the info message date should also change
        del form_data['info_message']
        assert_editing_machine_makes_info_message_date_equal(with_time(base_datetime, "04:00"))
        self.assertEqual(self.machine.info_message, "")
