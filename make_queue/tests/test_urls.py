from abc import ABC
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_time
from django_hosts import reverse

from news.models import Event, TimePlace
from users.models import User
from util.test_utils import CleanUpTempFilesTestMixin, Get, MOCK_JPG_FILE, assert_requesting_paths_succeeds
from ..models.course import Printer3DCourse
from ..models.machine import Machine, MachineType, MachineUsageRule
from ..models.reservation import Quota, Reservation, ReservationRule


class MakeQueueTestBase(CleanUpTempFilesTestMixin, ABC):

    # noinspection PyAttributeOutsideInit
    def init_objs(self):
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.sewing_machine_type = MachineType.objects.get(pk=2)
        self.printer1 = Machine.objects.create(name="Printer 1", machine_type=self.printer_machine_type)
        self.printer2 = Machine.objects.create(name="Printer 2", machine_type=self.printer_machine_type)
        self.sewing1 = Machine.objects.create(name="Sewing 1", machine_type=self.sewing_machine_type)
        self.sewing2 = Machine.objects.create(name="Sewing 2", machine_type=self.sewing_machine_type)
        self.machines = (self.printer1, self.printer2, self.sewing1, self.sewing2)

        self.rule1 = ReservationRule.objects.create(
            machine_type=self.printer_machine_type, start_time=parse_time("00:00"), days_changed=0, end_time=parse_time("18:00"),
            start_days=127, max_hours=6, max_inside_border_crossed=6,
        )
        self.rule2 = ReservationRule.objects.create(
            machine_type=self.printer_machine_type, start_time=parse_time("18:00"), days_changed=1, end_time=parse_time("00:00"),
            start_days=127, max_hours=10, max_inside_border_crossed=6,
        )
        self.rule3 = ReservationRule.objects.create(
            machine_type=self.sewing_machine_type, start_time=parse_time("00:00"), days_changed=1, end_time=parse_time("00:00"),
            start_days=127, max_hours=4, max_inside_border_crossed=4,
        )
        self.rules = (self.rule1, self.rule2, self.rule3)

        self.usage_rule1 = MachineUsageRule.objects.create(machine_type=self.printer_machine_type, content="lorem ipsum dolor sit amet")
        self.usage_rule2 = MachineUsageRule.objects.create(machine_type=self.sewing_machine_type, content="LOREM IPSUM DOLOR SIT AMET")

        self.user1 = User.objects.create_user("user1")
        self.user2 = User.objects.create_user("user2")
        self.course1 = Printer3DCourse.objects.create(
            user=self.user1, username=self.user1.username, date=timezone.localdate(), status=Printer3DCourse.Status.ACCESS,
        )
        self.course2 = Printer3DCourse.objects.create(
            user=self.user2, username=self.user2.username, date=timezone.localdate(), status=Printer3DCourse.Status.REGISTERED,
        )

        self.user1.user_permissions.add(Permission.objects.get(codename='can_create_event_reservation'))

        self.quota1 = Quota.objects.create(all=True, machine_type=self.printer_machine_type, number_of_reservations=3)
        self.quota2 = Quota.objects.create(all=True, machine_type=self.sewing_machine_type)
        self.quota3 = Quota.objects.create(user=self.user1, machine_type=self.printer_machine_type, number_of_reservations=10)
        self.quota4 = Quota.objects.create(user=self.user1, machine_type=self.sewing_machine_type, diminishing=True)
        self.quota5 = Quota.objects.create(user=self.user2, machine_type=self.printer_machine_type, ignore_rules=True)
        self.quotas = (self.quota1, self.quota2, self.quota3, self.quota4, self.quota5)

        now = timezone.localtime()
        self.event1 = Event.objects.create(title="Event 1", content="Lorem ipsum dolor sit amet", clickbait="Please!", image=MOCK_JPG_FILE)
        self.timeplace1 = TimePlace.objects.create(
            event=self.event1, end_time=now + timedelta(hours=3), place="Makerverkstedet", place_url="https://makentnu.no/",
            hidden=False, number_of_tickets=10,
        )

        self.reservation1 = Reservation.objects.create(
            user=self.user1, machine=self.printer1, start_time=now, end_time=now + timedelta(hours=2), comment="Lorem ipsum dolor sit amet",
        )
        self.reservation2 = Reservation.objects.create(
            user=self.user1, machine=self.printer1, start_time=now + timedelta(hours=2), end_time=now + timedelta(hours=5), event=self.timeplace1,
        )
        self.reservation3 = Reservation.objects.create(
            user=self.user1, machine=self.sewing1, start_time=now, end_time=now + timedelta(hours=4), special=True, special_text="Gotta clean them",
        )
        self.reservation4 = Reservation.objects.create(
            user=self.user1, machine=self.sewing2, start_time=now, end_time=now + timedelta(hours=1), quota=self.quota4,
        )
        self.reservation5 = Reservation.objects.create(
            user=self.user2, machine=self.printer2, start_time=now, end_time=now + timedelta(hours=2.5), quota=self.quota5,
        )
        self.reservations = (self.reservation1, self.reservation2, self.reservation3, self.reservation4, self.reservation5)


class UrlTests(MakeQueueTestBase, TestCase):

    def setUp(self):
        self.init_objs()

    def test_all_get_request_paths_succeed(self):
        year, week_number, _weekday = timezone.localtime().isocalendar()
        path_predicates = [
            # urlpatterns
            Get(reverse('machine_list'), public=True),

            # machine_urlpatterns
            Get(reverse('create_machine'), public=False),
            *[
                Get(reverse('edit_machine', kwargs={'pk': machine.pk}), public=False)
                for machine in self.machines
            ],

            # Back to urlpatterns
            Get(reverse('machine_detail', kwargs={'year': year, 'week': week_number, 'machine': self.printer1}), public=True),

            # calendar_urlpatterns
            *[
                Get(reverse('api_reservation_rules', kwargs={'machine': machine}), public=True)
                for machine in self.machines
            ],

            # json_urlpatterns
            *[
                Get(reverse('reservation_json', kwargs={'machine': machine}), public=False)
                for machine in self.machines
            ],
            *[
                Get(reverse('reservation_json', kwargs={'machine': reservation.machine, 'reservation': reservation}), public=False)
                for reservation in self.reservations
            ],
            Get(reverse('user_json', kwargs={'username': self.user1.username}), public=False),
            Get(reverse('user_json', kwargs={'username': self.user2.username}), public=False),

            # Back to urlpatterns
            *[
                Get(reverse('create_reservation', kwargs={'machine': machine}), public=False)
                for machine in self.machines
            ],
            *[
                Get(reverse('edit_reservation', kwargs={'reservation': reservation}), public=False)
                for reservation in self.reservations if reservation != self.reservation2  # `reservation2` starts in the future
            ],
            Get(reverse('my_reservations_list'), public=False),
            Get(reverse('MAKE_reservations_list'), public=False),
            Get(reverse('find_free_slot'), public=True),

            # rules_urlpatterns
            Get(reverse('reservation_rule_list', kwargs={'machine_type': self.printer_machine_type}), public=True),
            Get(reverse('reservation_rule_list', kwargs={'machine_type': self.sewing_machine_type}), public=True),
            Get(reverse('create_reservation_rule', kwargs={'machine_type': self.printer_machine_type}), public=False),
            Get(reverse('create_reservation_rule', kwargs={'machine_type': self.sewing_machine_type}), public=False),
            *[
                Get(reverse('edit_reservation_rule', kwargs={'machine_type': rule.machine_type, 'pk': rule.pk}), public=False)
                for rule in self.rules
            ],
            Get(reverse('machine_usage_rules_detail', kwargs={'machine_type': self.printer_machine_type}), public=True),
            Get(reverse('machine_usage_rules_detail', kwargs={'machine_type': self.sewing_machine_type}), public=True),
            Get(reverse('edit_machine_usage_rules', kwargs={'machine_type': self.printer_machine_type}), public=False),
            Get(reverse('edit_machine_usage_rules', kwargs={'machine_type': self.sewing_machine_type}), public=False),

            # quota_urlpatterns
            Get(reverse('quota_panel'), public=False),
            Get(reverse('create_quota'), public=False),
            *[
                Get(reverse('edit_quota', kwargs={'pk': quota.pk}), public=False)
                for quota in self.quotas
            ],
            Get(reverse('user_quota_list', kwargs={'user': self.user1}), public=False),
            Get(reverse('user_quota_list', kwargs={'user': self.user2}), public=False),
            Get(reverse('quota_panel', kwargs={'user': self.user1}), public=False),
            Get(reverse('quota_panel', kwargs={'user': self.user2}), public=False),

            # course_urlpatterns
            Get(reverse('course_registration_list'), public=False),
            Get(reverse('create_course_registration'), public=False),
            Get(reverse('create_course_registration_success'), public=False),
            Get(reverse('edit_course_registration', kwargs={'pk': self.course1.pk}), public=False),
            Get(reverse('edit_course_registration', kwargs={'pk': self.course2.pk}), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)
