from http import HTTPStatus
from typing import Optional, Type
from urllib.parse import urlparse

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.forms import BaseForm
from django.test import Client, TestCase, override_settings
from django.urls import path
from django_hosts import reverse

from internal.tests.test_urls import INTERNAL_CLIENT_DEFAULTS, reverse_internal
from users.models import User
from util.auth_utils import get_perm
from web.tests.test_urls import ADMIN_CLIENT_DEFAULTS
from web.urls import urlpatterns as base_urlpatterns
from . import hosts_and_internal_urls_override
from .hosts_and_internal_urls_override import urlpatterns as internal_urlpatterns_override
from ..forms import ContentBoxForm, EditSourceContentBoxForm
from ..models import ContentBox
from ..views import DisplayContentBoxView, EditContentBoxView


TEST_TITLE = 'test_title'
TEST_MULTI_TITLES = ('test_main', 'test_alt1', 'test_alt2')

urlpatterns = base_urlpatterns
urlpatterns += [
    DisplayContentBoxView.get_path(TEST_TITLE),
    *DisplayContentBoxView.get_multi_path(*TEST_MULTI_TITLES),
]


# Uses the imported (and modified) `urlpatterns` as the base urlpatterns
@override_settings(ROOT_URLCONF=__name__)
class SimpleModelAndViewTests(TestCase):

    def setUp(self):
        self.content_box1 = ContentBox.objects.create(title=TEST_TITLE)
        self.edit_url1 = reverse('contentbox_edit', args=[self.content_box1.pk])

    def test_str(self):
        self.assertEqual(self.content_box1.title, TEST_TITLE)
        self.assertEqual(str(self.content_box1), self.content_box1.title)

    def test_get_content_box_retrieves_correctly(self):
        paths_to_test = (reverse(TEST_TITLE), f'/{TEST_TITLE}/')
        for path in paths_to_test:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('contentbox', response.context)
                self.assertEqual(response.context['contentbox'].title, TEST_TITLE)

    def test_all_paths_of_multi_path_content_box_retrieve_correctly(self):
        multi_path_content_box_title = TEST_MULTI_TITLES[0]
        paths_to_test = (
            reverse(multi_path_content_box_title),
            *(f'/{url}/' for url in TEST_MULTI_TITLES),
        )
        for path in paths_to_test:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('contentbox', response.context)
                self.assertEqual(response.context['contentbox'].title, multi_path_content_box_title)

    def test_visiting_edit_page_is_only_allowed_for_users_with_permission(self):
        user = User.objects.create_user(username="user1")
        user.add_perms('contentbox.change_contentbox')
        user_client = Client()
        user_client.force_login(user)
        anon_client = Client()

        self.assertGreaterEqual(anon_client.get(self.edit_url1).status_code, 300)
        self.assertEqual(user_client.get(self.edit_url1).status_code, HTTPStatus.OK)

    def test_edit_page_contains_correct_error_messages(self):
        user = User.objects.create_user(username="user1")
        user.add_perms('contentbox.change_contentbox')
        self.client.force_login(user)

        def assert_response_contains_error_message(posted_content: str, error: bool):
            data = {
                subwidget_name: posted_content for subwidget_name in ContentBoxForm.CONTENT_SUBWIDGET_NAMES
            }
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

        def assert_edit_page_response_with(*, status_code: int, form: Optional[Type[BaseForm]]):
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


INTERNAL_TEST_TITLE = 'internal_test_title'
internal_change_perm = 'contentbox.perm1'


class InternalDisplayContentBoxView(DisplayContentBoxView):
    extra_context = {
        'base_template': 'internal/base.html',
    }

    change_perms = (internal_change_perm,)


# Insert this path at the beginning of the internal urlpatterns (overridden in `hosts_and_internal_urls_override.py`),
# to make it override the already defined ContentBox change path
internal_urlpatterns_override.insert(0, path(
    "contentbox/<int:pk>/edit/",
    permission_required(internal_change_perm, raise_exception=True)(EditContentBoxView.as_view(base_template='internal/base.html')),
    name='contentbox_edit',
))
internal_urlpatterns_override.append(
    InternalDisplayContentBoxView.get_path(INTERNAL_TEST_TITLE)
)


# Uses the imported (and modified) `urlpatterns` as the base urlpatterns
@override_settings(ROOT_URLCONF=__name__)
# Uses the `host_patterns` of this file as the base host_patterns
@override_settings(ROOT_HOSTCONF=hosts_and_internal_urls_override.__name__)
class MultiSubdomainTests(TestCase):

    def setUp(self):
        Permission.objects.create(
            codename=internal_change_perm.split('.')[1],
            name="Change internal content box",
            content_type=ContentType.objects.get_for_model(ContentBox),
        )

        self.internal_user = User.objects.create_user("internal_user")
        self.internal_admin = User.objects.create_user("internal_admin", is_staff=True)
        self.internal_user.add_perms('internal.is_internal', 'contentbox.change_contentbox')
        self.internal_admin.add_perms('internal.is_internal', 'contentbox.change_contentbox', internal_change_perm)

        self.internal_user_public_client = Client()
        self.internal_user_internal_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_user_admin_client = Client(**ADMIN_CLIENT_DEFAULTS)
        self.internal_admin_public_client = Client()
        self.internal_admin_internal_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_admin_admin_client = Client(**ADMIN_CLIENT_DEFAULTS)

        self.internal_user_public_client.force_login(self.internal_user)
        self.internal_user_internal_client.force_login(self.internal_user)
        self.internal_user_admin_client.force_login(self.internal_user)
        self.internal_admin_public_client.force_login(self.internal_admin)
        self.internal_admin_internal_client.force_login(self.internal_admin)
        self.internal_admin_admin_client.force_login(self.internal_admin)

        # Creates the content boxes by requesting them
        self.internal_user_public_client.get(reverse(TEST_TITLE))
        self.internal_user_internal_client.get(reverse_internal(INTERNAL_TEST_TITLE))
        self.public_content_box = ContentBox.objects.get(title=TEST_TITLE)
        self.internal_content_box = ContentBox.objects.get(title=INTERNAL_TEST_TITLE)

        self.public_edit_url = reverse('contentbox_edit', kwargs={'pk': self.public_content_box.pk})
        self.public_admin_edit_url = reverse('admin:contentbox_contentbox_change', args=[self.public_content_box.pk], host='admin')
        self.internal_edit_url = reverse_internal('contentbox_edit', pk=self.internal_content_box.pk)
        self.internal_admin_edit_url = reverse('admin:contentbox_contentbox_change', args=[self.internal_content_box.pk], host='admin')

    def test_content_box_edit_urls_are_only_accessible_with_required_permissions(self):
        # Users with the `'change_contentbox'` permission can edit public content boxes
        self.assertEqual(self.internal_user_public_client.get(self.public_edit_url).status_code, HTTPStatus.OK)
        self.assertEqual(self.internal_admin_public_client.get(self.public_edit_url).status_code, HTTPStatus.OK)

        def assert_staff_can_change_through_django_admin(can_change: bool, client: Client, url: str):
            response = client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(response.context['has_change_permission'], can_change)
            form_fields = response.context['adminform'].form.fields
            # If the user does not have the change permission, the form should not contain any fields, as the page will be read-only
            self.assertEqual(bool(form_fields), can_change)

        # Only users with the `internal_change_perm` permission can edit internal content boxes
        self.assertGreaterEqual(self.internal_user_internal_client.get(self.internal_edit_url).status_code, 400)
        self.assertEqual(self.internal_admin_internal_client.get(self.internal_edit_url).status_code, HTTPStatus.OK)
        # Only staff can change content boxes through Django admin
        self.assertRedirects(self.internal_user_admin_client.get(self.public_admin_edit_url),
                             f"/login/?next={urlparse(self.public_admin_edit_url).path}")
        self.assertRedirects(self.internal_user_admin_client.get(self.internal_admin_edit_url),
                             f"/login/?next={urlparse(self.internal_admin_edit_url).path}")
        assert_staff_can_change_through_django_admin(True, self.internal_admin_admin_client, self.public_admin_edit_url)
        assert_staff_can_change_through_django_admin(True, self.internal_admin_admin_client, self.internal_admin_edit_url)

        extra_perm = Permission.objects.create(
            codename='extra_perm',
            name="Extra internal content box perm",
            content_type=ContentType.objects.get_for_model(ContentBox),
        )
        self.internal_content_box.extra_change_permissions.add(extra_perm)
        # Users without the extra change permission for the content box, are not allowed to edit it
        self.assertGreaterEqual(self.internal_admin_internal_client.get(self.internal_edit_url).status_code, 400)
        assert_staff_can_change_through_django_admin(False, self.internal_admin_admin_client, self.internal_admin_edit_url)
        # Now `internal_admin` can edit it again:
        self.internal_admin.user_permissions.add(extra_perm)
        self.assertEqual(self.internal_admin_internal_client.get(self.internal_edit_url).status_code, HTTPStatus.OK)
        assert_staff_can_change_through_django_admin(True, self.internal_admin_admin_client, self.internal_admin_edit_url)
