from http import HTTPStatus

from django.conf import settings
from django.test import Client, TestCase

from contentbox.models import ContentBox
from users.models import User
from util.test_utils import Get, assertRedirectsWithPathPrefix, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs
from util.url_utils import reverse_internal
from ..forms import MemberStatusForm
from ..models import Member, Quote, Secret, SystemAccess


# Makes sure that the subdomain of all requests is `internal`
INTERNAL_CLIENT_DEFAULTS = {'SERVER_NAME': f'internal.{settings.PARENT_HOST}'}


class UrlTests(TestCase):

    def setUp(self):
        password = "TEST_PASS"
        non_member_user = User.objects.create_user(username="NON_MEMBER", password=password)
        member_user = User.objects.create_user(username="MEMBER", password=password)
        member_editor_user = User.objects.create_user(username="MEMBER_EDITOR", password=password)

        internal_perms = ('internal.is_internal', 'internal.view_member', 'internal.view_secret')
        member_user.add_perms(*internal_perms)
        member_editor_user.add_perms(*internal_perms,
                                     'internal.add_member', 'internal.can_edit_group_membership', 'internal.change_systemaccess')
        self.member = Member.objects.create(user=member_user)
        self.member_editor = Member.objects.create(user=member_editor_user)
        self.members = (self.member, self.member_editor)

        self.anon_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.non_member_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.member_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.member_editor_client = Client(**INTERNAL_CLIENT_DEFAULTS)

        self.all_clients = {self.anon_client, self.non_member_client, self.member_client, self.member_editor_client}

        self.non_member_client.login(username=non_member_user, password=password)
        self.member_client.login(username=member_user, password=password)
        self.member_editor_client.login(username=member_editor_user, password=password)

        self.home_content_box = ContentBox.objects.create(url_name='home')
        self.secret1 = Secret.objects.create(title="Key storage box", content="Code: 1234")
        self.secret2 = Secret.objects.create(title="YouTube account", content="<p>Email: make@gmail.com</p><p>Password: password</p>")
        self.secrets = (self.secret1, self.secret2)

        self.quote1 = Quote.objects.create(quote="Ha ha.", quoted="Human 1", author=member_user, date="2022-02-02")
        self.quote2 = Quote.objects.create(quote="I like human humor.", quoted="Human 2", author=member_editor_user,
                                           date="2022-02-02")
        self.quotes = (self.quote1, self.quote2)

    @staticmethod
    def generic_request(client: Client, method: str, path: str, data: dict = None):
        match method:
            case 'GET':
                return client.get(path)
            case 'POST':
                return client.post(path, data)
            case _:
                raise ValueError(f'Method "{method}" not supported')

    def _test_url_permissions(self, method: str, path: str, data: dict = None, *, allowed_clients: set[Client], expected_redirect_path: str = None):
        disallowed_clients = self.all_clients - allowed_clients
        for client in disallowed_clients:
            response = self.generic_request(client, method, path)
            # Anonymous users should be redirected to the login page:
            if client is self.anon_client:
                assertRedirectsWithPathPrefix(self, response, "/login/")
            # Disallowed members should be rejected:
            else:
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        for client in allowed_clients:
            response = self.generic_request(client, method, path, data)
            if expected_redirect_path:
                assertRedirectsWithPathPrefix(self, response, expected_redirect_path)
            else:
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def _test_internal_url(self, method: str, path: str, data: dict = None, *, expected_redirect_path: str = None):
        self._test_url_permissions(method, path, data, allowed_clients={self.member_client, self.member_editor_client},
                                   expected_redirect_path=expected_redirect_path)

    def _test_editor_url(self, method: str, path: str, data: dict = None, *, expected_redirect_path: str = None):
        self._test_url_permissions(method, path, data, allowed_clients={self.member_editor_client},
                                   expected_redirect_path=expected_redirect_path)

    def test_permissions(self):
        self._test_internal_url('GET', reverse_internal('member_list'))
        self._test_internal_url('GET', reverse_internal('member_detail', self.member.pk))
        self._test_editor_url('GET', reverse_internal('member_create'))

        # All members can edit themselves, but only editors can edit other members
        self._test_internal_url('GET', reverse_internal('member_update', self.member.pk))
        self._test_editor_url('GET', reverse_internal('member_update', self.member_editor.pk))

        self._test_editor_url('GET', reverse_internal('member_retire', self.member.pk))
        self._test_editor_url('GET', reverse_internal('member_quit', self.member.pk))

        path_data_assertion_tuples = (
            ('member_quit', {'date_quit_or_retired': "2000-01-01", 'reason_quit': "Whatever."}, lambda member: member.quit),
            ('member_status_update', {'status_action': MemberStatusForm.StatusAction.UNDO_QUIT}, lambda member: not member.quit),
            ('member_retire', {'date_quit_or_retired': "2002-01-01"}, lambda member: member.retired),
            ('member_status_update', {'status_action': MemberStatusForm.StatusAction.UNDO_RETIRE}, lambda member: not member.retired),
        )
        for path, data, assertion in path_data_assertion_tuples:
            with self.subTest(path=path, data=data):
                self._test_editor_url('POST', reverse_internal(path, self.member.pk), data,
                                      expected_redirect_path=f"/members/{self.member.pk}/")
                self.member.refresh_from_db()
                self.assertTrue(assertion(self.member))

        for system_access in self.member.system_accesses.all():
            with self.subTest(system_access=system_access):
                # No one is allowed to change their `WEBSITE` access. Other than that,
                # all members can edit their own accesses, but only editors can edit other members'.
                allowed_clients = {self.member_client, self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
                self._test_url_permissions('POST', reverse_internal('system_access_update', self.member.pk, system_access.pk),
                                           {'value': True}, allowed_clients=allowed_clients,
                                           expected_redirect_path=f"/members/{self.member.pk}/")

        for system_access in self.member_editor.system_accesses.all():
            with self.subTest(system_access=system_access):
                # No one is allowed to change their `WEBSITE` access
                allowed_clients = {self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
                self._test_url_permissions('POST', reverse_internal('system_access_update', self.member_editor.pk, system_access.pk),
                                           {'value': True}, allowed_clients=allowed_clients,
                                           expected_redirect_path=f"/members/{self.member_editor.pk}/")

        self._test_internal_url('GET', reverse_internal('home'))

        self._test_internal_url('POST', reverse_internal('set_language'), {'language': 'en'}, expected_redirect_path="/en/")
        self._test_internal_url('POST', reverse_internal('set_language'), {'language': 'nb'}, expected_redirect_path="/")

    def test_all_non_member_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse_internal(self.home_content_box.url_name), public=False),
            Get(reverse_internal('content_box_update', self.home_content_box.pk), public=False),

            Get(reverse_internal('secret_list'), public=False),
            Get(reverse_internal('secret_create'), public=False),
            Get(reverse_internal('secret_update', self.secret1.pk), public=False),
            Get(reverse_internal('secret_update', self.secret2.pk), public=False),

            Get(reverse_internal('quote_list'), public=False),
            Get(reverse_internal('quote_create'), public=False),
            Get(reverse_internal('quote_update', self.quote1.pk), public=False),
            Get(reverse_internal('quote_update', self.quote2.pk), public=False),

            Get('/robots.txt', public=True, translated=False),
            Get('/.well-known/security.txt', public=True, translated=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'internal')

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Member, self.members)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(SystemAccess, [access
                                                                                           for member in self.members
                                                                                           for access in member.system_accesses.all()])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Secret, self.secrets)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Quote, self.quotes)
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
