from django.test import TestCase
from django_hosts import reverse

from users.models import User
from ..utility import template_view_get_context_data
from ...models.machine import MachineType
from ...models.reservation import Quota
from ...views.admin.quota import QuotaPanelView


class TestUserQuotaListView(TestCase):

    def test_get_user_quota(self):
        user = User.objects.create_user("test")
        user.add_perms('make_queue.change_quota')
        user2 = User.objects.create_user("test2")
        machine_type = MachineType.objects.first()
        Quota.objects.create(all=True, user=user, machine_type=machine_type, number_of_reservations=2)
        quota2 = Quota.objects.create(user=user, machine_type=machine_type, number_of_reservations=2)
        Quota.objects.create(user=user2, machine_type=machine_type, number_of_reservations=2)

        self.client.force_login(user)
        context_data = self.client.get(reverse('user_quota_list', args=[user])).context
        self.assertListEqual(list(context_data['user_quotas']), [quota2])


class TestQuotaPanelView(TestCase):

    def setUp(self):
        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        self.printer_machine_type = MachineType.objects.get(pk=1)
        self.sewing_machine_type = MachineType.objects.get(pk=2)
        self.user = User.objects.create_user("test")
        self.user2 = User.objects.create_user("test2")
        self.quota1 = Quota.objects.create(all=True, machine_type=self.sewing_machine_type, number_of_reservations=2)
        self.quota2 = Quota.objects.create(all=True, machine_type=self.printer_machine_type, number_of_reservations=4)
        self.quota3 = Quota.objects.create(user=self.user, machine_type=self.printer_machine_type,
                                           number_of_reservations=4)
        self.quota4 = Quota.objects.create(user=self.user2, machine_type=self.sewing_machine_type,
                                           number_of_reservations=1)

    def test_without_user(self):
        context_data = template_view_get_context_data(QuotaPanelView, request_user=self.user)
        self.assertListEqual(list(context_data["users"]), [self.user, self.user2])
        self.assertListEqual(list(context_data["global_quotas"]), [self.quota1, self.quota2])
        self.assertEqual(context_data["requested_user"], None)

    def test_with_user(self):
        context_data = template_view_get_context_data(QuotaPanelView, request_user=self.user, user=self.user)
        self.assertListEqual(list(context_data["users"]), [self.user, self.user2])
        self.assertListEqual(list(context_data["global_quotas"]), [self.quota1, self.quota2])
        self.assertEqual(context_data["requested_user"], self.user)
