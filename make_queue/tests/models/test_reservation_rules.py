from datetime import timedelta
from typing import Tuple

from django.test import TestCase
from django.utils.dateparse import parse_datetime, parse_time

from ...forms import ReservationRuleForm
from ...models.machine import MachineType
from ...models.reservation import ReservationRule


Period = ReservationRule.Period


class PeriodTests(TestCase):

    def setUp(self):
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.machine_type = MachineType.objects.get(pk=1)

    @staticmethod
    def round_hours_overlap(exact_weekday_range1: Tuple[float, float], exact_weekday_range2: Tuple[float, float]):
        return round(Period.hours_overlap(exact_weekday_range1, exact_weekday_range2), 2)

    def test_hours_overlap_inside(self):
        self.assertEqual(self.round_hours_overlap((1.25, 1.5),
                                                  (1.25, 1.4)), 3.6)
        self.assertEqual(self.round_hours_overlap((7, 2),
                                                  (1, 2)), 24)
        self.assertEqual(self.round_hours_overlap((7, 2),
                                                  (7, 1)), 24)
        self.assertEqual(self.round_hours_overlap((7, 2),
                                                  (7.4, 1.6)), 28.8)

    def test_hours_overlap_outside(self):
        self.assertEqual(Period.hours_overlap((1.2, 1.4),
                                              (1, 1.2)), 0)
        self.assertEqual(Period.hours_overlap((1.2, 1.4),
                                              (1.4, 1.8)), 0)
        self.assertEqual(Period.hours_overlap((7, 2),
                                              (3, 4)), 0)
        self.assertEqual(Period.hours_overlap((2, 3),
                                              (7, 2)), 0)

    def test_hours_overlap_borders_crossed(self):
        self.assertEqual(self.round_hours_overlap((1.2, 1.4),
                                                  (1.1, 1.35)), 3.6)
        self.assertEqual(self.round_hours_overlap((1.2, 1.4),
                                                  (1.25, 2.6)), 3.6)
        self.assertEqual(self.round_hours_overlap((1.2, 1.4),
                                                  (7, 3)), 4.8)
        self.assertEqual(self.round_hours_overlap((7, 2),
                                                  (1.1, 1.35)), 6)
        self.assertEqual(self.round_hours_overlap((7, 2),
                                                  (6.25, 7.25)), 6)
        self.assertEqual(self.round_hours_overlap((7, 2),
                                                  (6.25, 2.25)), 48)

    def test_overlap_self(self):
        period = Period(1, parse_time("10:00"), parse_time("14:00"), 0)

        self.assertTrue(period.overlap(period), "A period should overlap itself")

    def test_overlap_other(self):
        period1 = Period(1, parse_time("10:00"), parse_time("14:00"), 0)
        period2 = Period(1, parse_time("8:00"), parse_time("10:00"), 0)

        self.assertFalse(period1.overlap(period2), "A period that starts at another's end point should not overlap")
        self.assertFalse(period2.overlap(period1), "A period that ends at another's start point should not overlap")

        period3 = Period(1, parse_time("9:00"), parse_time("11:00"), 0)

        self.assertTrue(period1.overlap(period3), "A period that starts within another should overlap")
        self.assertTrue(period3.overlap(period1), "A period that starts within another should overlap")

        period4 = Period(2, parse_time("8:00"), parse_time("12:00"), 0)

        self.assertFalse(period1.overlap(period4), "Periods on distinct days should not overlap")
        self.assertFalse(period4.overlap(period1), "Periods on distinct days should not overlap")


class ReservationRuleTests(TestCase):

    def setUp(self):
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.machine_type = MachineType.objects.get(pk=1)

    def test_time_periods(self):
        rule = ReservationRule(start_time=parse_time("10:00"), end_time=parse_time("6:00"), days_changed=1,
                               start_days=[1, 3, 5, 6], max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)

        time_periods = rule.time_periods
        correct_time_periods = [
            Period.from_rule(1, rule),
            Period.from_rule(3, rule),
            Period.from_rule(5, rule),
            Period.from_rule(6, rule),
        ]

        self.assertEqual(len(time_periods), len(correct_time_periods))

        for calculated_period, correct_period in zip(time_periods, correct_time_periods):
            self.assertEqual(calculated_period.exact_start_weekday, correct_period.exact_start_weekday)
            self.assertEqual(calculated_period.exact_end_weekday, correct_period.exact_end_weekday)
            self.assertTrue(calculated_period.overlap(correct_period))
            hours_overlap = Period.hours_overlap((calculated_period.exact_start_weekday, calculated_period.exact_end_weekday),
                                                 (correct_period.exact_start_weekday, correct_period.exact_end_weekday))
            self.assertEqual(round(hours_overlap, 2), 20)

    def test_form_validation_for_single_rules_validates_expectedly(self):
        form_data = {
            'start_time': parse_time("10:00"), 'end_time': parse_time("6:00"), 'days_changed': 1,
            'start_days': [1, 3, 5, 6], 'max_inside_border_crossed': 0, 'machine_type': self.machine_type, 'max_hours': 0,
        }
        self.assertTrue(ReservationRuleForm(data=form_data).is_valid(),
                        "A rule with a difference of less than 24h between start_time and end_time should not overlap with itself")

        form_data = {
            'start_time': parse_time("10:00"), 'end_time': parse_time("12:00"), 'days_changed': 1,
            'start_days': [1, 2], 'max_inside_border_crossed': 0, 'machine_type': self.machine_type, 'max_hours': 0,
        }
        self.assertFalse(ReservationRuleForm(data=form_data).is_valid(),
                         "A rule with periods of more than 24h cannot have two successive days")

        form_data = {
            'start_time': parse_time("10:00"), 'end_time': parse_time("12:00"), 'days_changed': 1,
            'start_days': [1, 7], 'max_inside_border_crossed': 0, 'machine_type': self.machine_type, 'max_hours': 0,
        }
        self.assertFalse(ReservationRuleForm(data=form_data).is_valid(),
                         "A rule with periods of more than 24h cannot have two successive days")

        form_data = {
            'start_time': parse_time("10:00"), 'end_time': parse_time("12:00"), 'days_changed': 7,
            'start_days': [1], 'max_inside_border_crossed': 0, 'machine_type': self.machine_type, 'max_hours': 0,
        }
        self.assertFalse(ReservationRuleForm(data=form_data).is_valid(), "A rule cannot cover more than a week")

        form_data = {
            'start_time': parse_time("10:00"), 'end_time': parse_time("12:00"), 'days_changed': 0,
            'start_days': [], 'max_inside_border_crossed': 0, 'machine_type': self.machine_type, 'max_hours': 0,
        }
        self.assertFalse(ReservationRuleForm(data=form_data).is_valid(), "A rule must specify at least one start day")
        form_data['start_days'] = [1]
        self.assertTrue(ReservationRuleForm(data=form_data).is_valid())

    def test_form_validation_between_multiple_rules_validates_expectedly(self):
        ReservationRule.objects.create(
            start_time=parse_time("10:00"), end_time=parse_time("6:00"), days_changed=1,
            start_days=[1, 3, 5, 6], max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0,
        )

        form_data = {
            'start_time': parse_time("12:00"), 'end_time': parse_time("18:00"), 'days_changed': 0,
            'start_days': [2, 7], 'max_inside_border_crossed': 0, 'machine_type': self.machine_type, 'max_hours': 0,
        }
        self.assertTrue(ReservationRuleForm(data=form_data).is_valid())

        form_data = {
            'start_time': parse_time("5:00"), 'end_time': parse_time("12:00"), 'days_changed': 0,
            'start_days': [2], 'max_inside_border_crossed': 0, 'machine_type': self.machine_type, 'max_hours': 0,
        }
        self.assertFalse(ReservationRuleForm(data=form_data).is_valid())
        form_data['machine_type'] = MachineType.objects.get(pk=2)
        self.assertTrue(ReservationRuleForm(data=form_data).is_valid(),
                        "Rules for different machine types should not effect the validity of each other")

    def test_is_valid_time_in_rule_no_border_cross(self):
        rule = ReservationRule(start_time=parse_time("10:00"), end_time=parse_time("6:00"), days_changed=1,
                               start_days=[1], max_inside_border_crossed=5, machine_type=self.machine_type, max_hours=10)

        self.assertTrue(rule.valid_time_in_rule(parse_datetime("2018-11-05 10:12"),
                                                parse_datetime("2018-11-05 10:48"), False))
        self.assertTrue(rule.valid_time_in_rule(parse_datetime("2018-11-05 10:00"),
                                                parse_datetime("2018-11-05 20:00"), False))
        self.assertTrue(rule.valid_time_in_rule(parse_datetime("2018-11-05 20:00"),
                                                parse_datetime("2018-11-06 04:00"), False))

        self.assertFalse(rule.valid_time_in_rule(parse_datetime("2018-11-05 10:00"),
                                                 parse_datetime("2018-11-05 21:00"), False))
        self.assertFalse(rule.valid_time_in_rule(parse_datetime("2018-11-05 18:00"),
                                                 parse_datetime("2018-11-06 06:00"), False))

    def test_is_valid_time_in_rule_border_cross(self):
        rule = ReservationRule(start_time=parse_time("10:00"), end_time=parse_time("6:00"), days_changed=1,
                               start_days=[1], max_inside_border_crossed=5, machine_type=self.machine_type, max_hours=10)

        self.assertTrue(rule.valid_time_in_rule(parse_datetime("2018-11-05 08:00"),
                                                parse_datetime("2018-11-05 12:00"), True))
        self.assertTrue(rule.valid_time_in_rule(parse_datetime("2018-11-05 00:00"),
                                                parse_datetime("2018-11-05 15:00"), True))

        self.assertFalse(rule.valid_time_in_rule(parse_datetime("2018-11-05 09:00"),
                                                 parse_datetime("2018-11-05 16:00"), True))

    def test_is_valid_time_max_interval(self):
        self.assertFalse(ReservationRule.valid_time(parse_datetime("2018-11-05 00:00"),
                                                    parse_datetime("2018-11-12 00:01"),
                                                    self.machine_type),
                         """
                         Reservations should not be valid if they are longer than 1 week, as the logic won't work 
                         correctly. Reservations can still be longer than 1 week if they are allowed to ignore the
                         rules.
                         """)

    def test_is_valid_time(self):
        ReservationRule(start_time=parse_time("10:00"), end_time=parse_time("6:00"), days_changed=1,
                        start_days=[1], max_inside_border_crossed=5, machine_type=self.machine_type, max_hours=10).save()
        ReservationRule(start_time=parse_time("6:00"), end_time=parse_time("12:00"), days_changed=2,
                        start_days=[2], max_inside_border_crossed=16, machine_type=self.machine_type, max_hours=16).save()

        self.assertTrue(ReservationRule.valid_time(parse_datetime("2018-11-05 12:00"),
                                                   parse_datetime("2018-11-05 18:00"), self.machine_type),
                        "Periods that cover only one rule, should be valid if they are valid in that rule")
        self.assertFalse(ReservationRule.valid_time(parse_datetime("2018-11-05 12:00"),
                                                    parse_datetime("2018-11-05 23:00"), self.machine_type),
                         "Periods that cover only one rule, should be valid if they are valid in that rule")
        self.assertTrue(ReservationRule.valid_time(parse_datetime("2018-11-06 12:00"),
                                                   parse_datetime("2018-11-07 03:00"), self.machine_type),
                        "Periods that cover only one rule, should be valid if they are valid in that rule")
        self.assertFalse(ReservationRule.valid_time(parse_datetime("2018-11-06 12:00"),
                                                    parse_datetime("2018-11-07 18:00"), self.machine_type),
                         "Periods that cover only one rule, should be valid if they are valid in that rule")

        self.assertTrue(ReservationRule.valid_time(parse_datetime("2018-11-06 03:00"),
                                                   parse_datetime("2018-11-06 18:00"), self.machine_type),
                        "A period may still be valid, even though its total duration is larger than what is allowed in"
                        "one of the rules it partially covers")

        self.assertFalse(ReservationRule.valid_time(parse_datetime("2018-11-06 01:00"),
                                                    parse_datetime("2018-11-06 22:00"), self.machine_type),
                         "A period may be valid in each rule, it can still be invalid due to its total duration")

        self.assertFalse(ReservationRule.valid_time(parse_datetime("2018-11-06 00:00"),
                                                    parse_datetime("2018-11-06 12:00"), self.machine_type),
                         "A period may not be valid in one of the rules is covers")

        self.assertTrue(ReservationRule.valid_time(parse_datetime("2018-11-06 00:00"),
                                                   parse_datetime("2018-11-06 10:00"), self.machine_type),
                        "A period may be valid, even though not all of its rules are valid, if it is still less than"
                        "the shortest maximum length of any of its rules.")

    def test_is_valid_time_no_rules(self):
        """
        Tests to check that `ReservationRule.valid_time` works correctly when there are no rules or a period is not
        covered by any rules.
        """
        start_time = parse_datetime("2021-03-03 12:00")
        end_time = start_time + timedelta(hours=6)
        is_valid = ReservationRule.valid_time(start_time, end_time, self.machine_type)
        self.assertFalse(is_valid, "A period should not be valid if there are no rules.")

        rule1 = ReservationRule(start_time=parse_time("10:00"), end_time=parse_time("11:00"), days_changed=0,
                                start_days=[1, 2, 3, 4, 5, 6, 7], max_inside_border_crossed=5, machine_type=self.machine_type, max_hours=10)
        rule1.save()
        is_valid = ReservationRule.valid_time(start_time, end_time, self.machine_type)
        self.assertFalse(is_valid, "A period should not be valid if it is not covered by any rules.")

        rule1.start_time = parse_time("12:00")
        rule1.end_time = parse_time("18:00")
        rule1.save()
        self.assertTrue(ReservationRule.valid_time(start_time, end_time, self.machine_type))

        # Create an empty period
        start_time = parse_datetime("2021-03-01 12:05")
        is_valid = ReservationRule.valid_time(start_time, start_time, self.machine_type)
        self.assertFalse(is_valid, "A period should not be valid if it is empty, i.e., not coverd by any rules.")
