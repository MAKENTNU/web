from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from util.test_utils import CleanUpTempFilesTestMixin, MOCK_JPG_FILE
from ...forms import TimePlaceForm
from ...models import Event


class FormTestCase(CleanUpTempFilesTestMixin, TestCase):

    def setUp(self):
        event = Event.objects.create(
            title='',
            image=MOCK_JPG_FILE,
            hidden=True,
            private=False,
        )
        self.valid_time_place_form_data = {
            "event": event,
            "publication_time": timezone.now() + timedelta(days=1),
            "start_time": timezone.now() + timedelta(days=2),
            "end_time": timezone.now() + timedelta(days=2, hours=2),
            "place": "Makerverkstedet",
            "place_url": "https://www.makentnu.no",
            "hidden": False,
            "number_of_tickets": 30,
        }

    def test_valid_time_place_form_data_is_valid(self):
        form = TimePlaceForm(data=self.valid_time_place_form_data)

        self.assertTrue(form.is_valid())

    def test_time_place_form_data_with_start_time_none_is_not_valid(self):
        form_data = self.valid_time_place_form_data
        form_data["start_time"] = None

        form = TimePlaceForm(data=form_data)

        self.assertFalse(form.is_valid())

    def test_time_place_form_data_with_end_time_none_is_not_valid(self):
        form_data = self.valid_time_place_form_data
        form_data["end_time"] = None

        form = TimePlaceForm(data=form_data)

        self.assertFalse(form.is_valid())
