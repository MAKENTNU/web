from unittest import mock

from django.test import TestCase

from ..locale_utils import parse_datetime_localized
from ..templatetags.datetime_tags import formatted_localtime


class TemplateTagTestCases(TestCase):
    def setUp(self):
        self.base_date = parse_datetime_localized("2017-12-23 12:34")

    @mock.patch("django.utils.timezone.now")
    def test_formatted_localtime_without_shift(self, now_mock):
        now_mock.return_value = self.base_date
        self.assertEqual(formatted_localtime(), "2017-12-23T12:34:00+01:00")

    @mock.patch("django.utils.timezone.now")
    def test_formatted_localtime_with_positive_shift(self, now_mock):
        now_mock.return_value = self.base_date
        self.assertEqual(
            formatted_localtime(shift_hours=5), "2017-12-23T17:34:00+01:00"
        )
        self.assertEqual(
            formatted_localtime(shift_hours=24), "2017-12-24T12:34:00+01:00"
        )

    @mock.patch("django.utils.timezone.now")
    def test_formatted_localtime_with_negative_shift(self, now_mock):
        now_mock.return_value = self.base_date
        self.assertEqual(
            formatted_localtime(shift_hours=-4), "2017-12-23T08:34:00+01:00"
        )
        self.assertEqual(
            formatted_localtime(shift_hours=-24), "2017-12-22T12:34:00+01:00"
        )
