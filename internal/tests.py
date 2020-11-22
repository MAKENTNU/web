from typing import Set
from urllib.parse import urlparse

from django.test import Client
from django_hosts import reverse

from users.models import User
from util.test_utils import PermissionsTestCase, assert_requesting_paths_succeeds
from .forms import MemberStatusForm
from .models import Member, Secret, SystemAccess


class UrlTests(PermissionsTestCase):

    def setUp(self):
        password = "TEST_PASS"
        non_member_user = User.objects.create_user(username="NON_MEMBER", password=password)
        member_user = User.objects.create_user(username="MEMBER", password=password)
        member_editor_user = User.objects.create_user(username="MEMBER_EDITOR", password=password)

        self.add_permissions(member_user, "is_internal")
        self.add_permissions(member_editor_user, "is_internal",
                             "can_register_new_member", "can_edit_group_membership", "change_systemaccess")
        self.member = Member.objects.create(user=member_user)
        self.member_editor = Member.objects.create(user=member_editor_user)

        client_defaults = {'SERVER_NAME': 'internal.testserver'}
        self.anon_client = Client(**client_defaults)
        self.non_member_client = Client(**client_defaults)
        self.member_client = Client(**client_defaults)
        self.member_editor_client = Client(**client_defaults)

        self.all_clients = {self.anon_client, self.non_member_client, self.member_client, self.member_editor_client}

        self.non_member_client.login(username=non_member_user, password=password)
        self.member_client.login(username=member_user, password=password)
        self.member_editor_client.login(username=member_editor_user, password=password)

    @staticmethod
    def reverse(viewname: str, **kwargs):
        return reverse(viewname, kwargs=kwargs, host='internal', host_args=['internal'])

    @staticmethod
    def generic_request(client: Client, method: str, path: str, data: dict = None):
        if method == 'GET':
            return client.get(path)
        elif method == 'POST':
            return client.post(path, data)
        else:
            raise ValueError(f'Method "{method}" not supported')

    def _test_url_permissions(self, method: str, path: str, data: dict = None, *, allowed_clients: Set[Client], expected_redirect_url: str = None):
        disallowed_clients = self.all_clients - allowed_clients
        for client in disallowed_clients:
            response = self.generic_request(client, method, path)
            # Unauthorized users should be redirected to login:
            if client in {self.anon_client, self.non_member_client}:
                self.assertEqual(response.status_code, 302)
                self.assertTrue(urlparse(response.url).path.startswith("/login/"))
            else:
                self.assertGreaterEqual(response.status_code, 400)
        for client in allowed_clients:
            response = self.generic_request(client, method, path, data)
            if expected_redirect_url:
                self.assertRedirects(response, expected_redirect_url)
            else:
                self.assertEqual(response.status_code, 200)

    def _test_internal_url(self, method: str, path: str, data: dict = None, *, expected_redirect_url: str = None):
        self._test_url_permissions(method, path, data, allowed_clients={self.member_client, self.member_editor_client},
                                   expected_redirect_url=expected_redirect_url)

    def _test_editor_url(self, method: str, path: str, data: dict = None, *, expected_redirect_url: str = None):
        self._test_url_permissions(method, path, data, allowed_clients={self.member_editor_client},
                                   expected_redirect_url=expected_redirect_url)

    def test_permissions(self):
        self._test_internal_url('GET', self.reverse("members"))
        self._test_internal_url('GET', self.reverse("members", pk=self.member.pk))
        self._test_editor_url('GET', self.reverse("add-member"))

        # All members can edit themselves, but only editors can edit other members
        self._test_internal_url('GET', self.reverse("edit-member", pk=self.member.pk))
        self._test_editor_url('GET', self.reverse("edit-member", pk=self.member_editor.pk))

        self._test_editor_url('GET', self.reverse("member-quit", pk=self.member.pk))

        path_data_assertion_tuples = (
            ("member-quit", {'date_quit': "2000-01-01", 'reason_quit': "Whatever."}, lambda member: member.quit),
            ("edit-member-status", {'status_action': MemberStatusForm.StatusAction.UNDO_QUIT}, lambda member: not member.quit),
            ("edit-member-status", {'status_action': MemberStatusForm.StatusAction.RETIRE}, lambda member: member.retired),
            ("edit-member-status", {'status_action': MemberStatusForm.StatusAction.UNDO_RETIRE}, lambda member: not member.retired),
        )
        for path, data, assertion in path_data_assertion_tuples:
            self._test_editor_url('POST', self.reverse(path, pk=self.member.pk), data,
                                  expected_redirect_url=f"/members/{self.member.pk}/")
            self.member.refresh_from_db()
            self.assertTrue(assertion(self.member))

        for system_access in self.member.system_accesses.all():
            with self.subTest(system_access=system_access):
                # No one is allowed to change their "website" access. Other than that,
                # all members can edit their own accesses, but only editors can edit other members'.
                allowed_clients = {self.member_client, self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
                self._test_url_permissions('POST', self.reverse("edit-system-access", member_pk=self.member.pk, pk=system_access.pk),
                                           {'value': True}, allowed_clients=allowed_clients,
                                           expected_redirect_url=f"/members/{self.member.pk}/")

        for system_access in self.member_editor.system_accesses.all():
            with self.subTest(system_access=system_access):
                # No one is allowed to change their "website" access
                allowed_clients = {self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
                self._test_url_permissions('POST', self.reverse("edit-system-access", member_pk=self.member_editor.pk, pk=system_access.pk),
                                           {'value': True}, allowed_clients=allowed_clients,
                                           expected_redirect_url=f"/members/{self.member_editor.pk}/")

        self._test_internal_url('GET', self.reverse("home"))

        self._test_internal_url('POST', self.reverse("set_language"), {"language": "en"}, expected_redirect_url="/en/")
        self._test_internal_url('POST', self.reverse("set_language"), {"language": "nb"}, expected_redirect_url="/")

    def test_all_non_member_get_request_paths_succeed(self):
        secret1 = Secret.objects.create(title="Key storage box", content="Code: 1234")
        secret2 = Secret.objects.create(title="YouTube account", content="<p>Email: make@gmail.com</p><p>Password: password</p>")

        paths_to_must_be_authenticated = {
            self.reverse('secrets'): True,
            self.reverse('create-secret'): True,
            self.reverse('edit-secret', pk=secret1.pk): True,
            self.reverse('edit-secret', pk=secret2.pk): True,
            '/robots.txt': False,
        }
        assert_requesting_paths_succeeds(self, paths_to_must_be_authenticated, 'internal')
