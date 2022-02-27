from http import HTTPStatus

from decorator_include import decorator_include
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.urls import path
from django_hosts import reverse

from internal.tests.test_urls import INTERNAL_CLIENT_DEFAULTS, reverse_internal
from users.models import User
from web.urls import urlpatterns as base_urlpatterns
from . import hosts_and_internal_urls_override
from .hosts_and_internal_urls_override import urlpatterns as internal_urlpatterns_override
from ..models import ContentBox
from ..urls import get_content_box_urlpatterns
from ..views import DisplayContentBoxView


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

        edit_url = reverse('contentbox_edit', kwargs={'pk': self.content_box1.pk})
        self.assertGreaterEqual(anon_client.get(edit_url).status_code, 300)
        self.assertEqual(user_client.get(edit_url).status_code, HTTPStatus.OK)

    def test_edit_page_contains_correct_error_messages(self):
        user = User.objects.create_user(username="user1")
        user.add_perms('contentbox.change_contentbox')
        self.client.force_login(user)
        edit_url = reverse('contentbox_edit', args=[self.content_box1.pk])

        def assert_response_contains_error_message(posted_content: str, error: bool):
            data = {
                'content_0': posted_content,
                'content_1': posted_content,
            }
            response = self.client.post(edit_url, data=data)
            # The form will redirect if valid, and stay on the same page if not
            self.assertEqual(response.status_code, 200 if error else 302)
            self.assertInHTML("Manglende språk", response.content.decode(), count=1 if error else 0)

        assert_response_contains_error_message("", True)
        assert_response_contains_error_message("asdf", False)


INTERNAL_TEST_TITLE = 'internal_test_title'
internal_change_perm = 'contentbox.perm1'

# Insert this path at the beginning of the internal urlpatterns (overridden in `hosts_and_internal_urls_override.py`),
# to make it effectively override the already defined content box paths
internal_urlpatterns_override.insert(0, path(
    "contentbox/", decorator_include(
        permission_required(internal_change_perm, raise_exception=True),
        get_content_box_urlpatterns(base_template='internal/base.html')
    )
))


class InternalDisplayContentBoxView(DisplayContentBoxView):
    extra_context = {
        'base_template': 'internal/base.html',
        'change_perm': 'contentbox.change_internal_contentbox',
    }


internal_urlpatterns_override += [
    InternalDisplayContentBoxView.get_path(INTERNAL_TEST_TITLE),
]


# Uses the imported (and modified) `urlpatterns` as the base urlpatterns
@override_settings(ROOT_URLCONF=__name__)
# Uses the `host_patterns` of this file as the base host_patterns
@override_settings(ROOT_HOSTCONF=hosts_and_internal_urls_override.__name__)
class MultiSubdomainTests(TestCase):

    def setUp(self):
        Permission.objects.create(
            codename=internal_change_perm.split('.')[1],
            name="Change internal contentbox",
            content_type=ContentType.objects.get_for_model(ContentBox),
        )

        internal_user = User.objects.create_user("internal_user")
        internal_admin = User.objects.create_user("internal_admin")
        internal_user.add_perms('internal.is_internal', 'contentbox.change_contentbox')
        internal_admin.add_perms('internal.is_internal', 'contentbox.change_contentbox', internal_change_perm)

        self.internal_user_public_client = Client()
        self.internal_user_internal_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_admin_public_client = Client()
        self.internal_admin_internal_client = Client(**INTERNAL_CLIENT_DEFAULTS)

        self.internal_user_public_client.force_login(internal_user)
        self.internal_user_internal_client.force_login(internal_user)
        self.internal_admin_public_client.force_login(internal_admin)
        self.internal_admin_internal_client.force_login(internal_admin)

        # Creates the content boxes by requesting them
        self.internal_user_public_client.get(reverse(TEST_TITLE))
        self.internal_user_internal_client.get(reverse_internal(INTERNAL_TEST_TITLE))
        public_content_box = ContentBox.objects.get(title=TEST_TITLE)
        internal_content_box = ContentBox.objects.get(title=INTERNAL_TEST_TITLE)

        self.public_edit_url = reverse('contentbox_edit', kwargs={'pk': public_content_box.pk})
        self.internal_edit_url = reverse_internal('contentbox_edit', pk=internal_content_box.pk)

    def test_content_box_edit_urls_are_only_accessible_with_required_permissions(self):
        # Users with the `'change_contentbox'` permission can edit public content boxes
        self.assertEqual(self.internal_user_public_client.get(self.public_edit_url).status_code, 200)
        self.assertEqual(self.internal_admin_public_client.get(self.public_edit_url).status_code, 200)

        # Only users with the `internal_change_perm` permission can edit internal content boxes
        self.assertGreaterEqual(self.internal_user_internal_client.get(self.internal_edit_url).status_code, 300)
        self.assertEqual(self.internal_admin_internal_client.get(self.internal_edit_url).status_code, 200)
