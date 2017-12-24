from django.test import TestCase
from datetime import datetime
from make_queue.views import ReservationCalendarView
from make_queue.models import Printer3D, SewingMachine


class ReservationCalendarViewTestCase(TestCase):

    def test_year_and_week_to_monday(self):
        date = datetime(2017, 12, 18)
        self.assertEqual(date, ReservationCalendarView.year_and_week_to_monday(2017, 51))

    def test_is_valid_week_with_zero_week_number(self):
        self.assertFalse(ReservationCalendarView.is_valid_week(2017, 0))

    def test_is_valid_week_with_valid_week(self):
        self.assertTrue(ReservationCalendarView.is_valid_week(2017, 51))

    def test_is_valid_week_with_to_high_week(self):
        self.assertFalse(ReservationCalendarView.is_valid_week(2017, 53))

    def test_get_next_valid_week_middle_of_year(self):
        self.assertEqual((2017, 30), ReservationCalendarView.get_next_valid_week(2017, 29, 1))
        self.assertEqual((2017, 28), ReservationCalendarView.get_next_valid_week(2017, 29, -1))

    def test_get_next_valid_week_year_shift(self):
        self.assertEqual((2018, 1), ReservationCalendarView.get_next_valid_week(2017, 52, 1))
        self.assertEqual((2016, 52), ReservationCalendarView.get_next_valid_week(2017, 1, -1))

    def test_date_to_percentage(self):
        self.assertEqual(41.875, ReservationCalendarView.date_to_percentage(datetime(2017, 12, 24, 10, 3)))
        self.assertEqual(50, ReservationCalendarView.date_to_percentage(datetime(2017, 12, 24, 12, 0)))

    def test_get_machines_simple_printer(self):
        Printer3D.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(Printer3D.objects.all()), list(ReservationCalendarView.get_machines(Printer3D.literal)))

    def test_get_machines_simple_sewing_machine(self):
        SewingMachine.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(SewingMachine.objects.all()),
                         list(ReservationCalendarView.get_machines(SewingMachine.literal)))

    def test_get_machines_several(self):
        Printer3D.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        Printer3D.objects.create(name="S2", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(Printer3D.objects.all()), list(ReservationCalendarView.get_machines(Printer3D.literal)))

    def test_get_machines_several_types(self):
        SewingMachine.objects.create(name="K1", location="U1", model="Generic", status="F")
        Printer3D.objects.create(name="S1", location="U1", model="Ultimaker", status="F")
        Printer3D.objects.create(name="S2", location="U1", model="Ultimaker", status="F")
        self.assertEqual(list(Printer3D.objects.all()), list(ReservationCalendarView.get_machines(Printer3D.literal)))
