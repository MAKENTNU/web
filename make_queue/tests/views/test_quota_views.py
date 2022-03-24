from typing import Optional

from django.test import Client, TestCase
from django_hosts import reverse

from users.models import User
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
        context_data = self.client.get(reverse('user_quota_list', args=[user.pk])).context
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

        self.superuser = User.objects.create_user("superuser", is_superuser=True)
        self.superuser_client = Client()
        self.superuser_client.force_login(self.superuser)

    def test_quota_panel_responds_with_expected_context(self):
        def assert_response_contains_expected_context(url: str, expected_requested_user: Optional[User]):
            response = self.superuser_client.get(url)
            context = response.context
            self.assertIsInstance(context['view'], QuotaPanelView)
            self.assertListEqual(list(context['users']), [self.user, self.user2, self.superuser])
            self.assertListEqual(list(context['global_quotas']), [self.quota1, self.quota2])
            self.assertEqual(context['requested_user'], expected_requested_user)

        assert_response_contains_expected_context(reverse('quota_panel'), None)
        assert_response_contains_expected_context(reverse('quota_panel', args=[self.user.pk]), self.user)
