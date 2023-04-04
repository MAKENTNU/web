from datetime import timedelta
from unittest import TestCase

from django.test import SimpleTestCase
from django.utils.dateparse import parse_datetime

from make_queue.models.reservation import ReservationRule
from ..locale_utils import exact_weekday_to_day_name, timedelta_to_hours, year_and_week_to_monday


class WeekUtilTest(SimpleTestCase):

    def test_exact_weekday_to_day_name_returns_expected_values(self):
        for week_offset in range(3):
            day_offset = week_offset * 7

            for day_index, day_name in ReservationRule.Day.choices:
                self.assertEqual(exact_weekday_to_day_name(day_offset + day_index), day_name)

            self.assertEqual(exact_weekday_to_day_name(day_offset + 1.000001), "Mandag")
            self.assertEqual(exact_weekday_to_day_name(day_offset + 1.999999), "Mandag")
            self.assertEqual(exact_weekday_to_day_name(day_offset + 7.999999), "Søndag")

    def test_year_and_week_to_monday(self):
        self.assertEqual(year_and_week_to_monday(2017, 51), parse_datetime("2017-12-18 00:00"))

    def test_year_and_week_to_monday_start_of_year(self):
        self.assertEqual(year_and_week_to_monday(2019, 1), parse_datetime("2018-12-31 00:00"))


class TimedeltaTest(TestCase):

    def test_hour_conversion(self):
        self.assertEqual(1, timedelta_to_hours(timedelta(hours=1)))
        self.assertEqual(1.25, timedelta_to_hours(timedelta(minutes=75)))
        self.assertEqual(0.05, timedelta_to_hours(timedelta(seconds=180)))
        self.assertEqual(28.25, timedelta_to_hours(timedelta(days=1, hours=3, minutes=60, seconds=900)))
