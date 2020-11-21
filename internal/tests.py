from typing import Set
from urllib.parse import urlparse

from django.test import Client, override_settings
from django_hosts import reverse

from users.models import User
from util.test_utils import PermissionsTestCase
from .models import Member, SystemAccess


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

        self.anon_client = Client()
        self.non_member_client = Client()
        self.member_client = Client()
        self.member_editor_client = Client()

        self.all_clients = {self.anon_client, self.non_member_client, self.member_client, self.member_editor_client}

        self.non_member_client.login(username=non_member_user, password=password)
        self.member_client.login(username=member_user, password=password)
        self.member_editor_client.login(username=member_editor_user, password=password)

    @staticmethod
    def get_path(name: str, args=None):
        return reverse(name, args, host="internal", host_args=["internal"])

    def _test_url_permissions(self, path: str, allowed_clients: Set[Client]):
        disallowed_clients = self.all_clients - allowed_clients
        for client in disallowed_clients:
            self.assertNotEqual(client.get(path, follow=True).status_code, 200)
        for client in allowed_clients:
            self.assertEqual(client.get(path, follow=True).status_code, 200)

    def _test_internal_url(self, path: str):
        self._test_url_permissions(path, {self.member_client, self.member_editor_client})

    def _test_editor_url(self, path: str):
        self._test_url_permissions(path, {self.member_editor_client})

    def _test_internal_post_url(self, path: str, data: dict, *, expected_redirect_url: str):
        # Unauthorized users should be redirected to login
        response = self.anon_client.post(path, data)
        self.assertTrue(urlparse(response.url).path.startswith("/login/"))
        response = self.non_member_client.post(path, data)
        self.assertTrue(urlparse(response.url).path.startswith("/login/"))

        self.assertRedirects(self.member_client.post(path, data), expected_redirect_url)
        self.assertRedirects(self.member_editor_client.post(path, data), expected_redirect_url)

    @override_settings(DEFAULT_HOST="internal")
    def test_permissions(self):
        self._test_internal_url(self.get_path("members"))
        self._test_internal_url(self.get_path("members", [self.member.pk]))
        self._test_editor_url(self.get_path("add-member"))

        # All members can edit themselves, but only editors can edit other members
        self._test_url_permissions(self.get_path("edit-member", [self.member.pk]),
                                   allowed_clients={self.member_client, self.member_editor_client})
        self._test_url_permissions(self.get_path("edit-member", [self.member_editor.pk]),
                                   allowed_clients={self.member_editor_client})

        self._test_editor_url(self.get_path("member-quit", [self.member.pk]))
        self._test_editor_url(self.get_path("member-undo-quit", [self.member.pk]))
        self._test_editor_url(self.get_path("member-retire", [self.member.pk]))
        self._test_editor_url(self.get_path("member-undo-retire", [self.member.pk]))

        for system_access in self.member.system_accesses.all():
            # No one is allowed to change their "website" access. Other than that,
            # all members can edit their own accesses, but only editors can edit other members'.
            allowed_clients = {self.member_client, self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
            self._test_url_permissions(self.get_path("toggle-system-access", [system_access.pk]),
                                       allowed_clients=allowed_clients)

        for system_access in self.member_editor.system_accesses.all():
            # No one is allowed to change their "website" access
            allowed_clients = {self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
            self._test_url_permissions(self.get_path("toggle-system-access", [system_access.pk]),
                                       allowed_clients=allowed_clients)

        self._test_internal_url(self.get_path("home"))

        self._test_internal_post_url(self.get_path("set_language"), {"language": "en"}, expected_redirect_url="/en/")
        self._test_internal_post_url(self.get_path("set_language"), {"language": "nb"}, expected_redirect_url="/")
