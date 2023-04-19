from abc import ABC
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.utils.http import urlencode
from django_hosts import reverse

from news.models import Event, TimePlace
from users.models import User
from util.test_utils import (
    CleanUpTempFilesTestMixin, Get, MOCK_JPG_FILE, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs,
)
from ..models.course import Printer3DCourse
from ..models.machine import Machine, MachineType, MachineUsageRule
from ..models.reservation import Quota, Reservation, ReservationRule


Day = ReservationRule.Day


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

        # `Day.values` is a list of all the weekdays
        self.rule1 = ReservationRule.objects.create(
            machine_type=self.printer_machine_type, start_time=parse_time("00:00"), days_changed=0, end_time=parse_time("18:00"),
            start_days=Day.values, max_hours=6, max_inside_border_crossed=6,
        )
        self.rule2 = ReservationRule.objects.create(
            machine_type=self.printer_machine_type, start_time=parse_time("18:00"), days_changed=1, end_time=parse_time("00:00"),
            start_days=Day.values, max_hours=10, max_inside_border_crossed=6,
        )
        self.rule3 = ReservationRule.objects.create(
            machine_type=self.sewing_machine_type, start_time=parse_time("00:00"), days_changed=1, end_time=parse_time("00:00"),
            start_days=Day.values, max_hours=4, max_inside_border_crossed=4,
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

        self.user1.add_perms('make_queue.can_create_event_reservation')

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
        # Create URL params to query all reservations
        api_reservation_list_url_params = urlencode({
            'startDate': Reservation.objects.earliest('start_time').start_time.isoformat(),
            'endDate': Reservation.objects.latest('end_time').end_time.isoformat(),
        })

        path_predicates = [
            # urlpatterns
            Get(reverse('machine_list'), public=True),

            # machine_urlpatterns
            Get(reverse('machine_create'), public=False),
            *[
                Get(reverse('machine_detail', args=[machine.pk]), public=True, redirect=True)
                for machine in self.machines
            ],
            *[
                Get(reverse('machine_update', args=[machine.pk]), public=False)
                for machine in self.machines
            ],

            # Back to urlpatterns
            *[
                Get(reverse('machine_detail', kwargs={'year': year, 'week': week_number, 'pk': machine.pk}), public=True)
                for machine in self.machines
            ],

            # calendar_urlpatterns
            *[
                Get(
                    f"{reverse('api_reservation_list', args=[machine.pk])}?{api_reservation_list_url_params}",
                    public=True,
                )
                for machine in self.machines
            ],
            *[
                Get(reverse('api_reservation_rule_list', args=[machine.pk]), public=True)
                for machine in self.machines
            ],

            # json_urlpatterns
            *[
                Get(reverse('api_machine_data', args=[machine.pk]), public=False)
                for machine in self.machines
            ],
            *[
                Get(reverse('api_machine_data', args=[reservation.machine.pk, reservation.pk]), public=False)
                for reservation in self.reservations
            ],

            # Back to urlpatterns
            *[
                Get(reverse('reservation_create', args=[machine.pk]), public=False)
                for machine in self.machines
            ],
            *[
                Get(reverse('reservation_update', args=[reservation.pk]), public=False)
                for reservation in self.reservations if reservation != self.reservation2  # `reservation2` starts in the future
            ],
            Get(reverse('reservation_my_list'), public=False),
            Get(reverse('admin_reservation_MAKE_list'), public=False),
            Get(reverse('reservation_find_free_slots'), public=False),

            # rules_urlpatterns
            Get(reverse('reservation_rule_list', args=[self.printer_machine_type.pk]), public=True),
            Get(reverse('reservation_rule_list', args=[self.sewing_machine_type.pk]), public=True),
            Get(reverse('reservation_rule_create', args=[self.printer_machine_type.pk]), public=False),
            Get(reverse('reservation_rule_create', args=[self.sewing_machine_type.pk]), public=False),
            *[
                Get(reverse('reservation_rule_update', args=[rule.machine_type.pk, rule.pk]), public=False)
                for rule in self.rules
            ],
            Get(reverse('machine_usage_rule_detail', args=[self.printer_machine_type.pk]), public=True),
            Get(reverse('machine_usage_rule_detail', args=[self.sewing_machine_type.pk]), public=True),
            Get(reverse('machine_usage_rule_update', args=[self.printer_machine_type.pk]), public=False),
            Get(reverse('machine_usage_rule_update', args=[self.sewing_machine_type.pk]), public=False),

            # quota_urlpatterns
            Get(reverse('admin_quota_panel'), public=False),
            Get(reverse('quota_create'), public=False),
            *[
                Get(reverse('quota_update', args=[quota.pk]), public=False)
                for quota in self.quotas
            ],
            Get(reverse('admin_user_quota_list', args=[self.user1.pk]), public=False),
            Get(reverse('admin_user_quota_list', args=[self.user2.pk]), public=False),
            Get(f"{reverse('admin_quota_panel')}?user={self.user1.pk}", public=False),
            Get(f"{reverse('admin_quota_panel')}?user={self.user2.pk}", public=False),

            # course_urlpatterns
            Get(reverse('printer_3d_course_list'), public=False),
            Get(reverse('printer_3d_course_create'), public=False),
            Get(reverse('printer_3d_course_update', args=[self.course1.pk]), public=False),
            Get(reverse('printer_3d_course_update', args=[self.course2.pk]), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Printer3DCourse, [self.course1, self.course2])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(MachineType, [self.printer_machine_type, self.sewing_machine_type])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(MachineUsageRule, [self.usage_rule1, self.usage_rule2])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Machine, self.machines)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Quota, self.quotas)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(ReservationRule, self.rules)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Reservation, self.reservations)
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
