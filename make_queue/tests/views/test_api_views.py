import datetime
from http import HTTPStatus
from typing import Dict

from django.test import TestCase
from django.urls import reverse

from ...models.machine import Machine, MachineType
from ...models.reservation import ReservationRule


class CalendarApiTestCase(TestCase):

    def setUp(self):
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.machine1 = self.create_machine("1", machine_type=self.printer_machine_type)
        self.valid_data_dates = {
            'startDate': '2021-01-01 10:20Z',
            'endDate': '2021-01-01 12:20Z',
        }
        

    def test_get_reservations_json_returns_empty_reservation_list(self):
        response = self.client.get(reverse('api_reservations',  args=[self.machine1]), data=self.valid_data_dates)
        self.assertStatusCodeAndJsonEqual(response, {'reservations': []})

    def test_get_api_reservation_rules_json_returns_reservation_rules_list(self):
        response = self.client.get(reverse('api_reservation_rules',  args=[self.machine1]),  data=self.valid_data_dates)
        self.assertStatusCodeAndJsonEqual(response, {'rules': []})

        rule = self.create_reservation_rule(
            start_time=datetime.time(10, 0),
            end_time=datetime.time(14, 0),
            machine_type=self.machine1.machine_type,
            start_days=0,
            days_changed=0,
            max_hours=1,
        )

        response = self.client.get(reverse('api_reservation_rules',  args=[self.machine1]),  data=self.valid_data_dates)
        self.assertStatusCodeAndJsonEqual(response, {'rules':  [{"periods": [], "max_inside": rule.max_hours, "max_crossed": 0.0}]})
        
    def assertStatusCodeAndJsonEqual(self, response, expected_json_dict: Dict, expected_status_code: HTTPStatus = HTTPStatus.OK):
        self.assertEqual(response.status_code, expected_status_code)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            expected_json_dict,
        )

    @staticmethod
    def create_machine(name_prefix: str, machine_type: MachineType, **kwargs) -> Machine:
        """Creates a machine of type ``machine_type`` with name '``name_prefix`` ``machine_type``'."""
        return Machine.objects.create(
            name=f"{name_prefix} {machine_type.name}",
            machine_type=machine_type,
            **kwargs,
        )

    def create_reservation_rule(self, start_time, end_time, machine_type, start_days=0, max_hours=0, max_inside_border_crossed=0, days_changed=0):
        return ReservationRule.objects.create(
            start_time=start_time,
            end_time=end_time,
            machine_type=machine_type,
            start_days=start_days,
            max_hours=max_hours,
            max_inside_border_crossed=max_inside_border_crossed,
            days_changed=days_changed,
        )