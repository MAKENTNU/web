from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ..templatetags.datetime_tags import formatted_localtime


class TemplateTagTestCases(TestCase):

    def setUp(self):
        self.base_date = parse_datetime("2017-12-23 12:34")

    @mock.patch('django.utils.timezone.now')
    def test_formatted_localtime_without_shift(self, now_mock):
        now_mock.return_value = timezone.get_default_timezone().localize(self.base_date)
        self.assertEqual("2017-12-23 12:34", formatted_localtime())

    @mock.patch('django.utils.timezone.now')
    def test_formatted_localtime_with_positive_shift(self, now_mock):
        now_mock.return_value = timezone.get_default_timezone().localize(self.base_date)
        self.assertEqual("2017-12-23 17:34", formatted_localtime(shift_hours=5))
        self.assertEqual("2017-12-24 12:34", formatted_localtime(shift_hours=24))

    @mock.patch('django.utils.timezone.now')
    def test_formatted_localtime_with_negative_shift(self, now_mock):
        now_mock.return_value = timezone.get_default_timezone().localize(self.base_date)
        self.assertEqual("2017-12-23 08:34", formatted_localtime(shift_hours=-4))
        self.assertEqual("2017-12-22 12:34", formatted_localtime(shift_hours=-24))
