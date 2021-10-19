from unittest import mock

from django.test import TestCase

from ..locale_utils import parse_datetime_localized
from ..templatetags.semantic_ui_calendar_extra import set_current_date


class TemplateTagTestCases(TestCase):

    def setUp(self):
        self.base_date = parse_datetime_localized("2017-12-23 12:34")

    @mock.patch('django.utils.timezone.now')
    def test_set_current_date_without_shift(self, now_mock):
        now_mock.return_value = self.base_date
        self.assertEqual("2017-12-23 12:34", set_current_date())

    @mock.patch('django.utils.timezone.now')
    def test_set_current_date_with_positive_shift(self, now_mock):
        now_mock.return_value = self.base_date
        self.assertEqual("2017-12-23 17:34", set_current_date(shift_hours=5))
        self.assertEqual("2017-12-24 12:34", set_current_date(shift_hours=24))

    @mock.patch('django.utils.timezone.now')
    def test_set_current_date_with_negative_shift(self, now_mock):
        now_mock.return_value = self.base_date
        self.assertEqual("2017-12-23 08:34", set_current_date(shift_hours=-4))
        self.assertEqual("2017-12-22 12:34", set_current_date(shift_hours=-24))
