from django.test import TestCase
from django.utils.datetime_safe import datetime

from make_queue.util.time import year_and_week_to_monday, is_valid_week, get_next_week


class WeekUtilTest(TestCase):

    def test_year_and_week_to_monday(self):
        date = datetime(2017, 12, 18)
        self.assertEqual(date, year_and_week_to_monday(2017, 51))

    def test_is_valid_week_with_zero_week_number(self):
        self.assertFalse(is_valid_week(2017, 0))

    def test_is_valid_week_with_valid_week(self):
        self.assertTrue(is_valid_week(2017, 51))

    def test_is_valid_week_with_to_high_week(self):
        self.assertFalse(is_valid_week(2017, 53))

    def test_get_next_valid_week_middle_of_year(self):
        self.assertEqual((2017, 30), get_next_week(2017, 29, 1))
        self.assertEqual((2017, 28), get_next_week(2017, 29, -1))

    def test_get_next_valid_week_year_shift(self):
        self.assertEqual((2018, 1), get_next_week(2017, 52, 1))
        self.assertEqual((2016, 52), get_next_week(2017, 1, -1))
