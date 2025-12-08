from http import HTTPStatus

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.templatetags.static import static
from django.test import Client, TestCase, override_settings
from django.urls import clear_url_caches

from contentbox.forms import EditSourceContentBoxForm
from contentbox.models import ContentBox
from users.models import User
from util.auth_utils import get_perms, perm_to_str
from util.url_utils import reverse_admin, reverse_internal
from web.multilingual.data_structures import MultiLingualTextStructure
from web.tests.test_urls import ADMIN_CLIENT_DEFAULTS
from .test_urls import INTERNAL_CLIENT_DEFAULTS
from ..models import Secret


class InternalContentBoxTests(TestCase):
    def setUp(self):
        internal_user = User.objects.create_user("internal_user")
        internal_admin = User.objects.create_user("internal_admin")
        internal_base_perms = ("internal.is_internal", "contentbox.change_contentbox")
        internal_admin_perms = (
            "contentbox.change_internal_contentbox",
            "internal.can_change_rich_text_source",
        )
        internal_user.add_perms(*internal_base_perms)
        internal_admin.add_perms(*internal_base_perms, *internal_admin_perms)

        self.internal_user_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_admin_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_user_client.force_login(internal_user)
        self.internal_admin_client.force_login(internal_admin)

        self.home_url = reverse_internal("home")
        # Creates the content box by requesting it
        self.internal_user_client.get(self.home_url)
        self.home_content_box = ContentBox.objects.get(url_name="home")
        # Add these extra change perms (mainly `internal.can_change_rich_text_source`),
        # so that the content box uses the form that allows editing the HTML source code
        self.home_content_box.extra_change_permissions.add(
            *get_perms(*internal_admin_perms)
        )
        self.home_edit_url = reverse_internal(
            "content_box_update", self.home_content_box.pk
        )

        self.internal_content_boxes = (self.home_content_box,)

    @classmethod
    def tearDownClass(cls):
        # Clear the cache again, after filling it with URLs prefixed with `/en`
        # when testing with the `LANGUAGE_CODE` setting set to `en` below
        clear_url_caches()

    def test_internal_content_boxes_can_only_be_edited_with_required_permission(self):
        self.assertEqual(
            self.internal_user_client.get(self.home_edit_url).status_code,
            HTTPStatus.FORBIDDEN,
        )
        self.assertEqual(
            self.internal_admin_client.get(self.home_edit_url).status_code,
            HTTPStatus.OK,
        )

    def test_internal_content_boxes_only_contain_visible_edit_buttons_when_user_has_required_permission(
        self,
    ):
        home_content_box_edit_path = f"/contentbox/{self.home_content_box.pk}/change/"

        def assert_visible_edit_button_in_response(
            should_button_be_present: bool, client: Client
        ):
            response_html = client.get(self.home_url).content.decode()
            self.assertEqual(
                "hidden edit-button" in response_html, not should_button_be_present
            )
            self.assertEqual(
                home_content_box_edit_path in response_html, should_button_be_present
            )

        assert_visible_edit_button_in_response(False, self.internal_user_client)
        assert_visible_edit_button_in_response(True, self.internal_admin_client)

    def test_home_content_box_allows_editing_source(self):
        response = self.internal_admin_client.get(self.home_edit_url)
        self.assertIs(type(response.context["form"]), EditSourceContentBoxForm)
        self.assertInHTML(
            f"""
            <script src="{static("ckeditor/ckeditor/config_from_django.js")}"
                    data-should-allow-all-tags="true"
                    id="config-from-django">
            </script>
            """,
            response.content.decode(),
            count=1,
        )
        # `editsource` is the name of the toolbar section containing the edit source button (see `CKEDITOR_CONFIGS` in the settings)
        self.assertContains(
            response,
            "&quot;editsource&quot;",
            # This view only uses one language, and so there should only be one occurrence of this string
            count=1,
        )

    @override_settings(LANGUAGE_CODE="nb")
    def test_internal_content_boxes_accept_posting_just_norwegian(self):
        self._test_internal_content_boxes_accept_posting_just_one_language()

    @override_settings(LANGUAGE_CODE="en")
    def test_internal_content_boxes_accept_posting_just_english(self):
        # Have to clear the cached URLs, to make calls to `reverse()` return paths that are not prefixed with `/en`
        # (after having overridden the `LANGUAGE_CODE` setting so that it's set to `en`)
        clear_url_caches()
        self._test_internal_content_boxes_accept_posting_just_one_language()

    def _test_internal_content_boxes_accept_posting_just_one_language(self):
        mock_content = "asdf"
        expected_content_languages = {
            language: mock_content
            for language in MultiLingualTextStructure.SUPPORTED_LANGUAGES
        }

        for content_box in self.internal_content_boxes:
            with self.subTest(content_box=content_box):
                edit_url = reverse_internal("content_box_update", content_box.pk)
                response = self.internal_admin_client.post(
                    edit_url,
                    {
                        f"title_{settings.LANGUAGE_CODE}": "Mock Title",
                        f"content_{settings.LANGUAGE_CODE}": mock_content,
                    },
                )
                display_url = reverse_internal(content_box.url_name)
                self.assertRedirects(response, display_url)
                content_box.refresh_from_db()
                content_text_structure: MultiLingualTextStructure = content_box.content
                # The content box should contain the same content for all languages
                self.assertEqual(
                    len(content_text_structure.languages),
                    len(expected_content_languages),
                )
                for language in expected_content_languages:
                    self.assertEqual(
                        content_text_structure[language],
                        expected_content_languages[language],
                    )


class SecretTests(TestCase):
    def setUp(self):
        self.normal_secret = Secret.objects.create(
            title="Storage key code", content="1234"
        )
        self.board_secret = Secret.objects.create(
            title="Code for deleting the organization", content="asdf"
        )

        self.board_perm = Permission.objects.create(
            codename="board_perm",
            name="Can view secrets that only members of the board need",
            content_type=ContentType.objects.get_for_model(Secret),
        )
        self.board_secret.extra_view_permissions.add(self.board_perm)

        self.member_user = User.objects.create_user("member_user")
        self.board_member_user = User.objects.create_user("board_member_user")
        # This superuser should not have any permissions added to their `user_permissions` or through groups,
        # to test that they have all permissions without having to grant any explicitly
        self.superuser = User.objects.create_user(
            "superuser", is_staff=True, is_superuser=True
        )

        base_secret_perms = (
            "internal.is_internal",
            "internal.view_secret",
            "internal.change_secret",
            "internal.delete_secret",
        )
        self.member_user.add_perms(*base_secret_perms)
        self.board_member_user.add_perms(
            *base_secret_perms, perm_to_str(self.board_perm)
        )

        self.member_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.board_member_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.superuser_client = Client(**INTERNAL_CLIENT_DEFAULTS)

        self.member_client.force_login(self.member_user)
        self.board_member_client.force_login(self.board_member_user)
        self.superuser_client.force_login(self.board_member_user)

    def test_only_secrets_users_have_permission_to_view_are_listed(self):
        secret_list_url = reverse_internal("secret_list")

        def assert_only_secrets_user_has_permission_to_view_are_listed(
            client: Client, *, board_member: bool
        ):
            response = client.get(secret_list_url)
            self.assertContains(response, self.normal_secret.title)
            self.assertContains(response, self.normal_secret.content)
            # `count=None` means at least once
            self.assertContains(
                response, self.board_secret.title, count=None if board_member else 0
            )
            self.assertContains(
                response, self.board_secret.content, count=None if board_member else 0
            )

        assert_only_secrets_user_has_permission_to_view_are_listed(
            self.member_client, board_member=False
        )
        assert_only_secrets_user_has_permission_to_view_are_listed(
            self.board_member_client, board_member=True
        )
        assert_only_secrets_user_has_permission_to_view_are_listed(
            self.superuser_client, board_member=True
        )

    def test_users_can_only_change_secrets_they_have_permission_to_view(self):
        def assert_users_can_change_secret(secret: Secret, *, is_board_secret: bool):
            change_url = reverse_internal("secret_update", secret.pk)
            self.assertEqual(
                self.member_client.get(change_url).status_code,
                HTTPStatus.FORBIDDEN if is_board_secret else HTTPStatus.OK,
            )
            self.assertEqual(
                self.board_member_client.get(change_url).status_code, HTTPStatus.OK
            )
            self.assertEqual(
                self.superuser_client.get(change_url).status_code, HTTPStatus.OK
            )

        assert_users_can_change_secret(self.normal_secret, is_board_secret=False)
        assert_users_can_change_secret(self.board_secret, is_board_secret=True)

    def test_users_can_only_delete_secrets_they_have_permission_to_view(self):
        def assert_user_can_delete_secret(
            client: Client, secret: Secret, *, can_delete: bool
        ):
            delete_url = reverse_internal("secret_delete", secret.pk)
            try:
                with transaction.atomic():
                    # `FOUND` means that the request was successful and that the client is redirected to the view's `success_url`
                    self.assertEqual(
                        client.delete(delete_url).status_code,
                        HTTPStatus.FOUND if can_delete else HTTPStatus.FORBIDDEN,
                    )
                    self.assertEqual(
                        Secret.objects.filter(pk=secret.pk).exists(), not can_delete
                    )
                    # Raise an error so that the transaction is rolled back
                    raise IntegrityError
            except IntegrityError:
                pass
            # Ensure that the deletion of the secret was rolled back (not strictly necessary to test)
            self.assertTrue(Secret.objects.filter(pk=secret.pk).exists())

        assert_user_can_delete_secret(
            self.member_client, self.normal_secret, can_delete=True
        )
        assert_user_can_delete_secret(
            self.board_member_client, self.normal_secret, can_delete=True
        )
        assert_user_can_delete_secret(
            self.superuser_client, self.normal_secret, can_delete=True
        )

        assert_user_can_delete_secret(
            self.member_client, self.board_secret, can_delete=False
        )
        assert_user_can_delete_secret(
            self.board_member_client, self.board_secret, can_delete=True
        )
        assert_user_can_delete_secret(
            self.superuser_client, self.board_secret, can_delete=True
        )

    def test_staff_can_only_view_or_delete_secrets_they_have_permission_to_view(self):
        # Make the users staff
        self.member_user.is_staff = True
        self.member_user.save()
        self.board_member_user.is_staff = True
        self.board_member_user.save()

        member__admin_client = Client(**ADMIN_CLIENT_DEFAULTS)
        board_member__admin_client = Client(**ADMIN_CLIENT_DEFAULTS)
        superuser__admin_client = Client(**ADMIN_CLIENT_DEFAULTS)

        member__admin_client.force_login(self.member_user)
        board_member__admin_client.force_login(self.board_member_user)
        superuser__admin_client.force_login(self.superuser)

        def assert_users_can_view_admin_page(path: str, *, is_board_secret: bool):
            self.assertEqual(
                member__admin_client.get(path).status_code,
                HTTPStatus.FORBIDDEN if is_board_secret else HTTPStatus.OK,
            )
            self.assertEqual(
                board_member__admin_client.get(path).status_code, HTTPStatus.OK
            )
            self.assertEqual(
                superuser__admin_client.get(path).status_code, HTTPStatus.OK
            )

        assert_users_can_view_admin_page(
            reverse_admin("internal_secret_change", args=[self.normal_secret.pk]),
            is_board_secret=False,
        )
        assert_users_can_view_admin_page(
            reverse_admin("internal_secret_change", args=[self.board_secret.pk]),
            is_board_secret=True,
        )

        assert_users_can_view_admin_page(
            reverse_admin("internal_secret_delete", args=[self.normal_secret.pk]),
            is_board_secret=False,
        )
        assert_users_can_view_admin_page(
            reverse_admin("internal_secret_delete", args=[self.board_secret.pk]),
            is_board_secret=True,
        )
