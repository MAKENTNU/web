from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from ..templatetags.semantic_ui_calendar_extra import set_current_date


class TemplateTagTestCases(TestCase):

    def setUp(self):
        self.base_date = datetime(2017, 12, 23, 12, 34, 0)

    @mock.patch('django.utils.timezone.now')
    def test_set_current_date_without_shift(self, now_mock):
        now_mock.return_value = timezone.get_default_timezone().localize(self.base_date)
        self.assertEqual("12/23/2017 12:34", set_current_date())

    @mock.patch('django.utils.timezone.now')
    def test_set_current_date_with_positive_shift(self, now_mock):
        now_mock.return_value = timezone.get_default_timezone().localize(self.base_date)
        self.assertEqual("12/23/2017 17:34", set_current_date(shift_hours=5))
        self.assertEqual("12/24/2017 12:34", set_current_date(shift_hours=24))

    @mock.patch('django.utils.timezone.now')
    def test_set_current_date_with_negative_shift(self, now_mock):
        now_mock.return_value = timezone.get_default_timezone().localize(self.base_date)
        self.assertEqual("12/23/2017 08:34", set_current_date(shift_hours=-4))
        self.assertEqual("12/22/2017 12:34", set_current_date(shift_hours=-24))
