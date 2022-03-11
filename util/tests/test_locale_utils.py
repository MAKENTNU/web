from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.datetime_safe import datetime

from make_queue.models.reservation import ReservationRule
from ..locale_utils import (
    date_to_local, exact_weekday_to_day_name, get_next_week, is_valid_week, local_to_date, timedelta_to_hours, year_and_week_to_monday,
)


class WeekUtilTest(TestCase):

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

    def test_is_valid_week_with_zero_week_number(self):
        self.assertFalse(is_valid_week(2017, 0))

    def test_is_valid_week_with_valid_week(self):
        self.assertTrue(is_valid_week(2017, 51))

    def test_is_valid_week_with_to_high_week(self):
        self.assertFalse(is_valid_week(2017, 53))

    def test_is_valid_week_with_to_high_week2(self):
        self.assertFalse(is_valid_week(2018, 53))

    def test_get_next_valid_week_middle_of_year(self):
        self.assertEqual((2017, 30), get_next_week(2017, 29, 1))
        self.assertEqual((2017, 28), get_next_week(2017, 29, -1))

    def test_get_next_valid_week_year_shift(self):
        self.assertEqual((2018, 1), get_next_week(2017, 52, 1))
        self.assertEqual((2016, 52), get_next_week(2017, 1, -1))


class TimedeltaTest(TestCase):

    def test_hour_conversion(self):
        self.assertEqual(1, timedelta_to_hours(timedelta(hours=1)))
        self.assertEqual(1.25, timedelta_to_hours(timedelta(minutes=75)))
        self.assertEqual(0.05, timedelta_to_hours(timedelta(seconds=180)))
        self.assertEqual(28.25, timedelta_to_hours(timedelta(days=1, hours=3, minutes=60, seconds=900)))


class LocalizationTest(TestCase):
    # Assumes the default timezone of the server is CET.
    # If the default timezone changes, so must the values in this test

    def test_local_to_date(self):
        local_date = datetime(2018, 3, 12, 11, 20, 20)
        self.assertEqual(timezone.datetime(2018, 3, 12, 10, 20, 20, tzinfo=timezone.utc),
                         local_to_date(local_date))

    def test_date_to_local(self):
        self.assertEqual(datetime(2018, 3, 12, 11, 20, 20).date(),
                         date_to_local(timezone.datetime(2018, 3, 12, 10, 20, 20, tzinfo=timezone.utc)).date())
        self.assertEqual(datetime(2018, 3, 12, 11, 20, 20).time(),
                         date_to_local(timezone.datetime(2018, 3, 12, 10, 20, 20, tzinfo=timezone.utc)).time())
