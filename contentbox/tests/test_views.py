from http import HTTPStatus

from django.test import Client, TestCase
from django_hosts import reverse

from users.models import User
from web.urls import urlpatterns as base_urlpatterns
from ..models import ContentBox
from ..views import DisplayContentBoxView


TEST_TITLE = 'test_title'
TEST_MULTI_TITLES = ('test_main', 'test_alt1', 'test_alt2')

base_urlpatterns += [
    DisplayContentBoxView.get_path(TEST_TITLE),
    *DisplayContentBoxView.get_multi_path(*TEST_MULTI_TITLES),
]


class ModelAndViewTests(TestCase):

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
