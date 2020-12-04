from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from news.models import Event, TimePlace
from ...forms import ReservationForm
from ...models.machine import Machine, MachineType


class ReservationFormTest(TestCase):

    def setUp(self):
        printer_machine_type = MachineType.objects.get(pk=1)
        self.machine = Machine.objects.create(name="Test", machine_model="Ultimaker 2+", machine_type=printer_machine_type)
        self.event = Event.objects.create(title="Test_Event")
        self.timeplace = TimePlace.objects.create(event=self.event)

    def test_valid_normal_reservation(self):
        form_data = {
            "start_time": timezone.now() + timedelta(hours=1),
            "end_time": timezone.now() + timedelta(hours=2),
            "machine_name": self.machine.pk,
        }
        form = ReservationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_machine_name(self):
        form_data = {
            "start_time": timezone.now() + timedelta(hours=1),
            "end_time": timezone.now() + timedelta(hours=2),
            # Since there is only one machine we can get an invalid primary key by just negating the current one
            "machine_name": not self.machine.pk,
        }

        form = ReservationForm(data=form_data)
        try:
            form.is_valid()
            self.fail("Reservations should not be allowed for machines that do not exist")
        except KeyError:
            pass

    def test_event_reservation(self):
        form_data = {
            "start_time": timezone.now() + timedelta(hours=1),
            "end_time": timezone.now() + timedelta(hours=2),
            "machine_name": self.machine.pk,
            "event": True,
            "event_pk": self.timeplace.pk,
        }

        form = ReservationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_event_reservation(self):
        form_data = {
            "start_time": timezone.now() + timedelta(hours=1),
            "end_time": timezone.now() + timedelta(hours=2),
            "machine_name": self.machine.pk,
            "event": True,
            # Since there is only one timeplace object we can invert its pk to get an invalid pk
            "event_pk": int(not self.timeplace.pk),
        }

        form = ReservationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_special_reservation(self):
        form_data = {
            "start_time": timezone.now() + timedelta(hours=1),
            "end_time": timezone.now() + timedelta(hours=2),
            "machine_name": self.machine.pk,
            "special": True,
            "special_text": "Test text",
        }

        form = ReservationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_special_reservation_with_too_long_text(self):
        form_data = {
            "start_time": timezone.now() + timedelta(hours=1),
            "end_time": timezone.now() + timedelta(hours=2),
            "machine_name": self.machine.pk,
            "special": True,
            "special_text": "a" * 201,
        }

        form = ReservationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_special_and_event_reservation(self):
        form_data = {
            "start_time": timezone.now() + timedelta(hours=1),
            "end_time": timezone.now() + timedelta(hours=2),
            "machine_name": self.machine.pk,
            "event": True,
            "event_pk": self.timeplace.pk,
            "special": True,
            "special_text": "Test text",
        }

        form = ReservationForm(data=form_data)
        self.assertFalse(form.is_valid())
