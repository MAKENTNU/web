from http import HTTPStatus

from django.test import Client, TestCase
from django_hosts import reverse

from users.models import User
from ...models.machine import MachineType
from ...models.reservation import Quota
from ...views.admin.quota import AdminQuotaPanelView


class TestAdminUserQuotaListView(TestCase):

    def test_get_user_quota(self):
        user = User.objects.create_user("test")
        user.add_perms('internal.is_internal', 'make_queue.change_quota')
        user2 = User.objects.create_user("test2")
        machine_type = MachineType.objects.first()
        Quota.objects.create(all=True, user=user, machine_type=machine_type, number_of_reservations=2)
        quota2 = Quota.objects.create(user=user, machine_type=machine_type, number_of_reservations=2)
        Quota.objects.create(user=user2, machine_type=machine_type, number_of_reservations=2)

        self.client.force_login(user)
        context_data = self.client.get(reverse('admin_user_quota_list', args=[user.pk])).context
        self.assertListEqual(list(context_data['user_quotas']), [quota2])


class TestAdminQuotaPanelView(TestCase):

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

        self.base_url = reverse('admin_quota_panel')

    def get_response(self, query: str):
        url = f"{self.base_url}?{query}" if query else self.base_url
        return self.superuser_client.get(url)

    def test_admin_quota_panel_responds_with_expected_context(self):
        def assert_response_contains(query: str, *, expected_requested_user: User | None):
            context = self.get_response(query).context
            self.assertIs(type(context['view']), AdminQuotaPanelView)
            self.assertListEqual(list(context['users']), [self.superuser, self.user, self.user2])
            self.assertListEqual(list(context['global_quotas']), [self.quota1, self.quota2])
            self.assertEqual(context['requested_user'], expected_requested_user)

        assert_response_contains("", expected_requested_user=None)
        assert_response_contains(f"user={self.user.pk}", expected_requested_user=self.user)

    def test_admin_quota_panel_responds_with_expected_errors(self):
        def assert_error_response_contains(query: str, *, expected_json_dict: dict):
            response = self.get_response(query)
            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertDictEqual(response.json(), expected_json_dict)

        field_required = "Feltet er påkrevet."
        user_404_not_found = "User with pk=404 was not found."
        undefined_asdf_field = {'undefined_fields': {'message': "These provided fields are not defined in the API.", 'fields': ['asdf']}}
        assert_error_response_contains("user=404", expected_json_dict={
            'field_errors': {'user': [user_404_not_found]}})
        assert_error_response_contains("asdf=asdf", expected_json_dict={
            'field_errors': {'user': [field_required]}, **undefined_asdf_field})
        assert_error_response_contains("user=404&asdf=asdf", expected_json_dict={
            'field_errors': {'user': [user_404_not_found]}, **undefined_asdf_field})
        assert_error_response_contains(f"user={self.user.pk}&asdf=asdf", expected_json_dict={
            **undefined_asdf_field})
