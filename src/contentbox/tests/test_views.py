from http import HTTPStatus
from typing import Type
from urllib.parse import urlparse

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.forms import BaseForm
from django.test import Client, TestCase, override_settings
from django_hosts import reverse

from users.models import User
from util.auth_utils import get_perm
from util.test_utils import assertRedirectsWithPathPrefix
from util.url_utils import reverse_admin
from web.multilingual.widgets import MultiLingualTextEdit
from web.tests.test_urls import ADMIN_CLIENT_DEFAULTS
from .urls import hosts, urls_main
from .urls.hosts import TEST_INTERNAL_CLIENT_DEFAULTS
from .urls.urls_internal import INTERNAL_TEST_URL_NAME, internal_change_perm
from .urls.urls_main import TEST_MULTI_URL_NAMES, TEST_URL_NAME
from ..forms import ContentBoxForm, EditSourceContentBoxForm
from ..models import ContentBox


@override_settings(ROOT_HOSTCONF=hosts.__name__, DEFAULT_HOST='test_main',
                   ROOT_URLCONF=urls_main.__name__)
class SimpleModelAndViewTests(TestCase):

    def setUp(self):
        self.content_box1 = ContentBox.objects.create(url_name=TEST_URL_NAME)
        self.edit_url1 = reverse('content_box_update', args=[self.content_box1.pk])

    def test_get_content_box_retrieves_correctly(self):
        paths_to_test = (reverse(TEST_URL_NAME), f'/{TEST_URL_NAME}/')
        for path in paths_to_test:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('contentbox', response.context)
                self.assertEqual(response.context['contentbox'].url_name, TEST_URL_NAME)

    def test_all_paths_of_multi_path_content_box_retrieve_correctly(self):
        multi_path_content_box_url_name = TEST_MULTI_URL_NAMES[0]
        paths_to_test = (
            reverse(multi_path_content_box_url_name),
            *(f'/{url}/' for url in TEST_MULTI_URL_NAMES),
        )
        for path in paths_to_test:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('contentbox', response.context)
                self.assertEqual(response.context['contentbox'].url_name, multi_path_content_box_url_name)

    def test_visiting_edit_page_is_only_allowed_for_users_with_permission(self):
        user = User.objects.create_user(username="user1")
        user.add_perms('contentbox.change_contentbox')
        user_client = Client()
        user_client.force_login(user)
        anon_client = Client()

        assertRedirectsWithPathPrefix(self, anon_client.get(self.edit_url1), "/login/")
        self.assertEqual(user_client.get(self.edit_url1).status_code, HTTPStatus.OK)

    def test_edit_page_contains_correct_error_messages(self):
        user = User.objects.create_user(username="user1")
        user.add_perms('contentbox.change_contentbox')
        self.client.force_login(user)

        def assert_response_contains_error_message(posted_content: str, error: bool):
            data = (
                    {subwidget_name: subwidget_name.title() for subwidget_name in MultiLingualTextEdit.get_subwidget_names('title')}
                    | {subwidget_name: posted_content for subwidget_name in MultiLingualTextEdit.get_subwidget_names('content')}
            )
            response = self.client.post(self.edit_url1, data=data)
            # The form will redirect if valid, and stay on the same page if not
            self.assertEqual(response.status_code, HTTPStatus.OK if error else HTTPStatus.FOUND)
            self.assertInHTML("Manglende språk", response.content.decode(), count=1 if error else 0)

        assert_response_contains_error_message("", True)
        assert_response_contains_error_message("asdf", False)

    def test_edit_view_has_expected_form_class(self):
        user = User.objects.create_user(username="user1")
        user.add_perms('contentbox.change_contentbox')
        self.client.force_login(user)

        def assert_edit_page_response_with(*, status_code: int, form: Type[BaseForm] | None):
            response = self.client.get(self.edit_url1)
            self.assertEqual(response.status_code, status_code)
            if form:
                self.assertEqual(type(response.context['form']), form)
            else:
                self.assertTrue(response.context is None or response.context.get('form') is None)

        # User is allowed, and form is the standard one
        assert_edit_page_response_with(status_code=HTTPStatus.OK, form=ContentBoxForm)

        can_change_rich_text_source_perm = 'internal.can_change_rich_text_source'
        self.content_box1.extra_change_permissions.add(get_perm(can_change_rich_text_source_perm))
        # User is not allowed
        assert_edit_page_response_with(status_code=HTTPStatus.FORBIDDEN, form=None)

        # User is allowed, and form is the one allowing editing HTML source code
        user.add_perms(can_change_rich_text_source_perm)
        assert_edit_page_response_with(status_code=HTTPStatus.OK, form=EditSourceContentBoxForm)


@override_settings(ROOT_HOSTCONF=hosts.__name__, DEFAULT_HOST='test_main',
                   ROOT_URLCONF=urls_main.__name__)
class MultiSubdomainTests(TestCase):

    def setUp(self):
        Permission.objects.create(
            codename=internal_change_perm.split('.')[1],
            name="Change internal content box",
            content_type=ContentType.objects.get_for_model(ContentBox),
        )

        self.internal_user = User.objects.create_user("internal_user")
        self.internal_admin = User.objects.create_user("internal_admin", is_staff=True)
        # This superuser should not have any permissions added to their `user_permissions` or through groups,
        # to test that they have all permissions without having to grant any explicitly
        self.superuser = User.objects.create_user("superuser", is_staff=True, is_superuser=True)
        change_content_box_perms = ('internal.is_internal', 'contentbox.change_contentbox')
        self.internal_user.add_perms(*change_content_box_perms)
        self.internal_admin.add_perms(*change_content_box_perms, internal_change_perm)

        self.internal_user__public_client = Client()
        self.internal_user__internal_client = Client(**TEST_INTERNAL_CLIENT_DEFAULTS)
        self.internal_user__admin_client = Client(**ADMIN_CLIENT_DEFAULTS)
        self.internal_admin__public_client = Client()
        self.internal_admin__internal_client = Client(**TEST_INTERNAL_CLIENT_DEFAULTS)
        self.internal_admin__admin_client = Client(**ADMIN_CLIENT_DEFAULTS)
        self.superuser__public_client = Client()
        self.superuser__internal_client = Client(**TEST_INTERNAL_CLIENT_DEFAULTS)
        self.superuser__admin_client = Client(**ADMIN_CLIENT_DEFAULTS)

        self.internal_user__public_client.force_login(self.internal_user)
        self.internal_user__internal_client.force_login(self.internal_user)
        self.internal_user__admin_client.force_login(self.internal_user)
        self.internal_admin__public_client.force_login(self.internal_admin)
        self.internal_admin__internal_client.force_login(self.internal_admin)
        self.internal_admin__admin_client.force_login(self.internal_admin)
        self.superuser__public_client.force_login(self.superuser)
        self.superuser__internal_client.force_login(self.superuser)
        self.superuser__admin_client.force_login(self.superuser)

        # Creates the content boxes by requesting them
        self.internal_user__public_client.get(reverse(TEST_URL_NAME))
        self.internal_user__internal_client.get(reverse(INTERNAL_TEST_URL_NAME, host='test_internal'))
        self.public_content_box = ContentBox.objects.get(url_name=TEST_URL_NAME)
        self.internal_content_box = ContentBox.objects.get(url_name=INTERNAL_TEST_URL_NAME)

        self.public_edit_url = reverse('content_box_update', args=[self.public_content_box.pk])
        self.public_admin_edit_url = reverse_admin('contentbox_contentbox_change', args=[self.public_content_box.pk])
        self.internal_edit_url = reverse('content_box_update', args=[self.internal_content_box.pk], host='test_internal')
        self.internal_admin_edit_url = reverse_admin('contentbox_contentbox_change', args=[self.internal_content_box.pk])

    def test_content_box_edit_urls_are_only_accessible_with_required_permissions(self):
        # Users with the `change_contentbox` permission can edit public content boxes
        self.assertEqual(self.internal_user__public_client.get(self.public_edit_url).status_code, HTTPStatus.OK)
        self.assertEqual(self.internal_admin__public_client.get(self.public_edit_url).status_code, HTTPStatus.OK)
        self.assertEqual(self.superuser__public_client.get(self.public_edit_url).status_code, HTTPStatus.OK)

        def assert_staff_can_change_through_django_admin(can_change: bool, client: Client, url: str):
            response = client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(response.context['has_change_permission'], can_change)
            form_fields = response.context['adminform'].form.fields
            # If the user does not have the change permission, the form should not contain any fields, as the page will be read-only
            self.assertEqual(bool(form_fields), can_change)

        # Only users with the `internal_change_perm` permission can edit internal content boxes
        self.assertEqual(self.internal_user__internal_client.get(self.internal_edit_url).status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(self.internal_admin__internal_client.get(self.internal_edit_url).status_code, HTTPStatus.OK)
        self.assertEqual(self.superuser__internal_client.get(self.internal_edit_url).status_code, HTTPStatus.OK)
        # Only staff can change content boxes through Django admin
        assert_staff_can_change_through_django_admin(True, self.internal_admin__admin_client, self.public_admin_edit_url)
        assert_staff_can_change_through_django_admin(True, self.internal_admin__admin_client, self.internal_admin_edit_url)
        assert_staff_can_change_through_django_admin(True, self.superuser__admin_client, self.public_admin_edit_url)
        assert_staff_can_change_through_django_admin(True, self.superuser__admin_client, self.internal_admin_edit_url)
        # Non-staff users are redirected to the login page by Django admin if they lack the required permissions
        self.assertRedirects(self.internal_user__admin_client.get(self.public_admin_edit_url),
                             f"/login/?next={urlparse(self.public_admin_edit_url).path}")
        self.assertRedirects(self.internal_user__admin_client.get(self.internal_admin_edit_url),
                             f"/login/?next={urlparse(self.internal_admin_edit_url).path}")

        extra_perm = Permission.objects.create(
            codename='extra_perm',
            name="Extra internal content box perm",
            content_type=ContentType.objects.get_for_model(ContentBox),
        )
        self.internal_content_box.extra_change_permissions.add(extra_perm)
        # Users without the extra change permission for the content box, are not allowed to edit it
        self.assertEqual(self.internal_admin__internal_client.get(self.internal_edit_url).status_code, HTTPStatus.FORBIDDEN)
        assert_staff_can_change_through_django_admin(False, self.internal_admin__admin_client, self.internal_admin_edit_url)
        # After granting `internal_admin` the extra change permission, they can edit the content box again:
        self.internal_admin.user_permissions.add(extra_perm)
        self.assertEqual(self.internal_admin__internal_client.get(self.internal_edit_url).status_code, HTTPStatus.OK)
        assert_staff_can_change_through_django_admin(True, self.internal_admin__admin_client, self.internal_admin_edit_url)
        # Superusers always have all permissions
        self.assertEqual(self.superuser__internal_client.get(self.internal_edit_url).status_code, HTTPStatus.OK)
        assert_staff_can_change_through_django_admin(True, self.superuser__admin_client, self.internal_admin_edit_url)
