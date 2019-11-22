from django.contrib.auth.models import User
from django.test import TestCase

from make_queue.fields import MachineTypeField
from make_queue.models.models import Quota
from make_queue.tests.utility import template_view_get_context_data
from make_queue.views.admin.quota import QuotaView
from make_queue.views.quota.user import GetUserQuotaView


class TestGetQuotaView(TestCase):

    def test_get_user_quota(self):
        user = User.objects.create_user("test")
        user2 = User.objects.create_user("test2")
        machine_type = MachineTypeField.get_machine_type(1)
        Quota.objects.create(all=True, user=user, machine_type=machine_type, number_of_reservations=2)
        quota2 = Quota.objects.create(user=user, machine_type=machine_type, number_of_reservations=2)
        Quota.objects.create(user=user2, machine_type=machine_type, number_of_reservations=2)

        context_data = template_view_get_context_data(GetUserQuotaView, request_user=user, user=user)
        context_data["user_quotas"] = list(context_data["user_quotas"])

        self.assertEqual(context_data, {"user_quotas": [quota2]})


class TestQuotaPanelView(TestCase):

    def setUp(self):
        self.machine_type_printer = MachineTypeField.get_machine_type(1)
        self.machine_type_sewing = MachineTypeField.get_machine_type(2)
        self.user = User.objects.create_user("test")
        self.user2 = User.objects.create_user("test2")
        self.quota1 = Quota.objects.create(all=True, machine_type=self.machine_type_sewing, number_of_reservations=2)
        self.quota2 = Quota.objects.create(all=True, machine_type=self.machine_type_printer, number_of_reservations=4)
        self.quota3 = Quota.objects.create(user=self.user, machine_type=self.machine_type_printer,
                                           number_of_reservations=4)
        self.quota4 = Quota.objects.create(user=self.user2, machine_type=self.machine_type_sewing,
                                           number_of_reservations=1)

    def test_without_user(self):
        context_data = template_view_get_context_data(QuotaView, request_user=self.user)
        self.assertEqual(list(context_data["users"]), [self.user, self.user2])
        self.assertEqual(list(context_data["global_quotas"]), [self.quota1, self.quota2])
        self.assertEqual(context_data["requested_user"], None)

    def test_with_user(self):
        context_data = template_view_get_context_data(QuotaView, request_user=self.user, user=self.user)
        self.assertEqual(list(context_data["users"]), [self.user, self.user2])
        self.assertEqual(list(context_data["global_quotas"]), [self.quota1, self.quota2])
        self.assertEqual(context_data["requested_user"], self.user)
