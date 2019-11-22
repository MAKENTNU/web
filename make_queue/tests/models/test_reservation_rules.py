import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from make_queue.fields import MachineTypeField
from make_queue.models.models import ReservationRule


class PeriodTests(TestCase):

    def setUp(self):
        self.period = ReservationRule.Period
        self.machine_type = MachineTypeField.get_machine_type(1)

    def test_hours_overlap_inside(self):
        self.assertEqual(round(self.period.hours_overlap(0.25, 0.5, 0.25, 0.4), 2), 3.6)
        self.assertEqual(round(self.period.hours_overlap(6, 1, 0, 1), 2), 24)
        self.assertEqual(round(self.period.hours_overlap(6, 1, 6, 0), 2), 24)
        self.assertEqual(round(self.period.hours_overlap(6, 1, 6.4, 0.6), 2), 28.8)

    def test_hours_overlap_outside(self):
        self.assertEqual(self.period.hours_overlap(0.2, 0.4, 0, 0.2), 0)
        self.assertEqual(self.period.hours_overlap(0.2, 0.4, 0.4, 0.8), 0)
        self.assertEqual(self.period.hours_overlap(6, 1, 2, 3), 0)
        self.assertEqual(self.period.hours_overlap(1, 2, 6, 1), 0)

    def test_hours_overlap_borders_crossed(self):
        self.assertEqual(round(self.period.hours_overlap(0.2, 0.4, 0.1, 0.35), 2), 3.6)
        self.assertEqual(round(self.period.hours_overlap(0.2, 0.4, 0.25, 1.6), 2), 3.6)
        self.assertEqual(round(self.period.hours_overlap(0.2, 0.4, 6, 2), 2), 4.8)
        self.assertEqual(round(self.period.hours_overlap(6, 1, 0.1, 0.35), 2), 6)
        self.assertEqual(round(self.period.hours_overlap(6, 1, 5.25, 6.25), 2), 6)
        self.assertEqual(round(self.period.hours_overlap(6, 1, 5.25, 1.25), 2), 48)

    def create_reservation_rule(self, start_time, end_time):
        return ReservationRule(start_time=start_time, end_time=end_time, start_days=0, max_hours=0,
                               max_inside_border_crossed=0, days_changed=0, machine_type=self.machine_type)

    def test_overlap_self(self):
        period = self.period(0, self.create_reservation_rule(datetime.time(10, 0), datetime.time(14, 0)))

        self.assertTrue(period.overlap(period), "A period should overlap itself")

    def test_overlap_other(self):
        period1 = self.period(0, self.create_reservation_rule(datetime.time(10, 0), datetime.time(14, 0)))
        period2 = self.period(0, self.create_reservation_rule(datetime.time(8, 0), datetime.time(10, 0)))

        self.assertFalse(period1.overlap(period2), "A period that starts at another's end point should not overlap")
        self.assertFalse(period2.overlap(period1), "A period that ends at another's start point should not overlap")

        period3 = self.period(0, self.create_reservation_rule(datetime.time(9, 0), datetime.time(11, 0)))

        self.assertTrue(period1.overlap(period3), "A period that starts within another should overlap")
        self.assertTrue(period3.overlap(period1), "A period that starts within another should overlap")

        period4 = self.period(1, self.create_reservation_rule(datetime.time(8, 0), datetime.time(12, 0)))

        self.assertFalse(period1.overlap(period4), "Periods on distinct days should not overlap")
        self.assertFalse(period4.overlap(period1), "Periods on distinct days should not overlap")


class ReservationRuleTests(TestCase):

    def setUp(self):
        self.machine_type = MachineTypeField.get_machine_type(1)

    def test_time_periods(self):
        rule = ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(6, 0), days_changed=1,
                               start_days=53, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)

        time_periods = rule.time_periods()
        correct_timeperiods = [
            rule.Period(0, rule),
            rule.Period(2, rule),
            rule.Period(4, rule),
            rule.Period(5, rule)
        ]

        self.assertEqual(len(time_periods), len(correct_timeperiods))

        for calculated_period, correct_period in zip(time_periods, correct_timeperiods):
            self.assertEqual(calculated_period.start_time, correct_period.start_time)
            self.assertEqual(calculated_period.end_time, correct_period.end_time)
            self.assertTrue(calculated_period.overlap(correct_period))
            self.assertEqual(
                round(rule.Period.hours_overlap(calculated_period.start_time, calculated_period.end_time,
                                                correct_period.start_time, correct_period.end_time), 2), 20)

    def test_is_valid_rule_internal(self):
        rule = ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(6, 0), days_changed=1,
                               start_days=53, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)
        self.assertTrue(rule.is_valid_rule(),
                        "A rule with a difference of less than 24h between start_time and end_time should not overlap with it self")

        rule = ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(12, 0), days_changed=1,
                               start_days=3, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)

        self.assertFalse(rule.is_valid_rule(), "A rule with periods of more than 24h cannot have two successive days")

        rule = ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(12, 0), days_changed=1,
                               start_days=65, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)

        self.assertFalse(rule.is_valid_rule(), "A rule with periods of more than 24h cannot have two successive days")
        try:
            rule.is_valid_rule(raise_error=True)
            self.fail("An exception should have been raised for a check on a non valid rule with raise_error set")
        except ValidationError:
            pass

        rule = ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(12, 0), days_changed=7,
                               start_days=1, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)

        self.assertFalse(rule.is_valid_rule(), "A rule cannot cover more than a week")
        try:
            rule.is_valid_rule(raise_error=True)
            self.fail("An exception should have been raised for a check on a non valid rule with raise_error set")
        except ValidationError:
            pass

    def test_is_valid_rule_external(self):
        ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(6, 0), days_changed=1,
                        start_days=53, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0).save()

        rule = ReservationRule(start_time=datetime.time(12, 0), end_time=datetime.time(18, 0), days_changed=0,
                               start_days=66, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)

        self.assertTrue(rule.is_valid_rule())

        rule = ReservationRule(start_time=datetime.time(5, 0), end_time=datetime.time(12, 0), days_changed=0,
                               start_days=2, max_inside_border_crossed=0, machine_type=self.machine_type, max_hours=0)

        self.assertFalse(rule.is_valid_rule())
        try:
            rule.is_valid_rule(raise_error=True)
            self.fail("An exception should have been raised for a check on a non valid rule with raise_error set")
        except ValidationError:
            pass

        try:
            rule.save()
            self.fail("Valid rules should not be saveable")
        except ValidationError:
            pass

        rule.machine_type = MachineTypeField.get_machine_type(2)
        self.assertTrue(rule.is_valid_rule(),
                        "Rules for different machine types should not effect the validity of each other")

    def test_is_valid_time_in_rule_no_border_cross(self):
        rule = ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(6, 0), days_changed=1,
                               start_days=1, max_inside_border_crossed=5, machine_type=self.machine_type, max_hours=10)

        self.assertTrue(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 10, 12),
                                                datetime.datetime(2018, 11, 5, 10, 48), False))
        self.assertTrue(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 10, 0),
                                                datetime.datetime(2018, 11, 5, 20, 0), False))
        self.assertTrue(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 20, 0),
                                                datetime.datetime(2018, 11, 6, 4, 0), False))

        self.assertFalse(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 10, 0),
                                                 datetime.datetime(2018, 11, 5, 21, 0), False))
        self.assertFalse(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 18, 0),
                                                 datetime.datetime(2018, 11, 6, 6, 0), False))

    def test_is_valid_time_in_rule_border_cross(self):
        rule = ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(6, 0), days_changed=1,
                               start_days=1, max_inside_border_crossed=5, machine_type=self.machine_type, max_hours=10)

        self.assertTrue(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 8, 0),
                                                datetime.datetime(2018, 11, 5, 12, 0), True))
        self.assertTrue(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 0, 0),
                                                datetime.datetime(2018, 11, 5, 15, 0), True))

        self.assertFalse(rule.valid_time_in_rule(datetime.datetime(2018, 11, 5, 9, 0),
                                                 datetime.datetime(2018, 11, 5, 16, 0), True))

    def test_is_valid_time_max_interval(self):
        self.assertFalse(ReservationRule.valid_time(datetime.datetime(2018, 11, 5, 0, 0),
                                                    datetime.datetime(2018, 11, 12, 0, 1),
                                                    self.machine_type),
                         """
                         Reservations should not be valid if they are longer than 1 week, as the logic won't work 
                         correctly. Reservations can still be longer than 1 week if they are allowed to ignore the
                         rules.
                         """)

    def test_is_valid_time(self):
        ReservationRule(start_time=datetime.time(10, 0), end_time=datetime.time(6, 0), days_changed=1,
                        start_days=1, max_inside_border_crossed=5, machine_type=self.machine_type, max_hours=10).save()
        ReservationRule(start_time=datetime.time(6, 0), end_time=datetime.time(12, 0), days_changed=2,
                        start_days=2, max_inside_border_crossed=16, machine_type=self.machine_type, max_hours=16).save()

        self.assertTrue(ReservationRule.valid_time(datetime.datetime(2018, 11, 5, 12, 0),
                                                   datetime.datetime(2018, 11, 5, 18, 0), self.machine_type),
                        "Periods that cover only one rule, should be valid if they are valid in that rule")
        self.assertFalse(ReservationRule.valid_time(datetime.datetime(2018, 11, 5, 12, 0),
                                                    datetime.datetime(2018, 11, 5, 23, 0), self.machine_type),
                         "Periods that cover only one rule, should be valid if they are valid in that rule")
        self.assertTrue(ReservationRule.valid_time(datetime.datetime(2018, 11, 6, 12, 0),
                                                   datetime.datetime(2018, 11, 7, 3, 0), self.machine_type),
                        "Periods that cover only one rule, should be valid if they are valid in that rule")
        self.assertFalse(ReservationRule.valid_time(datetime.datetime(2018, 11, 6, 12, 0),
                                                    datetime.datetime(2018, 11, 7, 18, 0), self.machine_type),
                         "Periods that cover only one rule, should be valid if they are valid in that rule")

        self.assertTrue(ReservationRule.valid_time(datetime.datetime(2018, 11, 6, 3, 0),
                                                   datetime.datetime(2018, 11, 6, 18, 0), self.machine_type),
                        "A period may still be valid, even though its total duration is larger than what is allowed in"
                        "one of the rules it partially covers")

        self.assertFalse(ReservationRule.valid_time(datetime.datetime(2018, 11, 6, 1, 0),
                                                    datetime.datetime(2018, 11, 6, 22, 0), self.machine_type),
                         "A period may be valid in each rule, it can still be invalid due to its total duration")

        self.assertFalse(ReservationRule.valid_time(datetime.datetime(2018, 11, 6, 0, 0),
                                                    datetime.datetime(2018, 11, 6, 12, 0), self.machine_type),
                         "A period may not be valid in one of the rules is covers")

        self.assertTrue(ReservationRule.valid_time(datetime.datetime(2018, 11, 6, 0, 0),
                                                   datetime.datetime(2018, 11, 6, 10, 0), self.machine_type),
                        "A period may be valid, even though not all of its rules are valid, if it is still less than"
                        "the shortest maximum length of any of its rules.")
