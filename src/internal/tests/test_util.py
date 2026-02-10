from unittest import TestCase as StandardTestCase

from django.utils.dateparse import parse_date

from ..util import date_to_semester, semester_to_year, year_to_semester


class UtilTests(StandardTestCase):
    def test_date_to_semester_returns_expected_result(self):
        self.assertEqual(date_to_semester(parse_date("2021-01-01")), "V21")
        self.assertEqual(date_to_semester(parse_date("2021-05-31")), "V21")
        self.assertEqual(date_to_semester(parse_date("2021-06-01")), "S21")
        self.assertEqual(date_to_semester(parse_date("2021-08-19")), "S21")
        self.assertEqual(date_to_semester(parse_date("2021-08-20")), "H21")
        self.assertEqual(date_to_semester(parse_date("2021-12-31")), "H21")
        self.assertEqual(date_to_semester(parse_date("2022-01-01")), "V22")

    def test_semester_to_year_returns_expected_result(self):
        # Test that both the long and the short way of denoting a year are interpreted correctly
        self.assertEqual(semester_to_year("V17"), 2017.0)
        self.assertEqual(semester_to_year("V2017"), 2017.0)
        self.assertEqual(semester_to_year("H17"), 2017.5)
        self.assertEqual(semester_to_year("H2017"), 2017.5)

        # Test that a number with a leading zero is interpreted correctly
        self.assertEqual(semester_to_year("V01"), 2001.0)
        self.assertEqual(semester_to_year("V2001"), 2001.0)
        self.assertEqual(semester_to_year("H01"), 2001.5)
        self.assertEqual(semester_to_year("H2001"), 2001.5)

        # Test that years in other centuries are interpreted correctly
        self.assertEqual(semester_to_year("V99"), 2099.0)
        self.assertEqual(semester_to_year("V1999"), 1999.0)
        self.assertEqual(semester_to_year("H99"), 2099.5)
        self.assertEqual(semester_to_year("H1999"), 1999.5)

    def test_year_to_semester_returns_expected_result(self):
        # Test that years with decimals other than .0 or .5 are rounded correctly
        self.assertEqual(year_to_semester(2017.0), "V17")
        self.assertEqual(year_to_semester(2017.01), "V17")
        self.assertEqual(year_to_semester(2017.49), "V17")
        self.assertEqual(year_to_semester(2017.5), "H17")
        self.assertEqual(year_to_semester(2017.99), "H17")

        # Test that results that should contain years with leading zeros, are returned correctly
        self.assertEqual(year_to_semester(2001.0), "V01")
        self.assertEqual(year_to_semester(2001.5), "H01")

        # Test that years in other centuries are returned correctly
        self.assertEqual(year_to_semester(2099.0), "V99")
        self.assertEqual(year_to_semester(1999.0), "V1999")
        self.assertEqual(year_to_semester(2099.5), "H99")
        self.assertEqual(year_to_semester(1999.5), "H1999")
