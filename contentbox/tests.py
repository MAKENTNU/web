from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from users.models import User
from .models import ContentBox


class ModelAndViewTests(TestCase):

    def setUp(self):
        self.contentbox1 = ContentBox.objects.create(title="TEST_TITLE")

    def test_str(self):
        self.assertEqual(self.contentbox1.title, "TEST_TITLE")
        self.assertEqual(str(self.contentbox1), self.contentbox1.title)

    def test_get_contentbox_retrieves_correctly(self):
        existing_contentbox_title = 'about'
        paths_to_test = (reverse(existing_contentbox_title), f'/{existing_contentbox_title}/')
        for path in paths_to_test:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('contentbox', response.context)
                self.assertEqual(response.context['contentbox'].title, existing_contentbox_title)

    def test_all_paths_of_multi_path_contentbox_retrieve_correctly(self):
        existing_multi_path_contentbox_urls = ('apply', 'søk', 'sok')
        existing_multi_path_contentbox_title = existing_multi_path_contentbox_urls[0]
        paths_to_test = (
            reverse(existing_multi_path_contentbox_title),
            *(f'/{url}/' for url in existing_multi_path_contentbox_urls),
        )
        for path in paths_to_test:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('contentbox', response.context)
                self.assertEqual(response.context['contentbox'].title, existing_multi_path_contentbox_title)

    def test_edit_without_permission_is_rejected(self):
        response = self.client.get(f'/contentbox/{self.contentbox1.pk}/edit/')
        self.assertNotEqual(response.status_code, 200)

    def test_edit_with_permission_succeeds(self):
        username = "TEST_USER"
        password = "TEST_PASS"
        user = User.objects.create_user(username=username, password=password)
        permission = Permission.objects.get(codename='change_contentbox')
        user.user_permissions.add(permission)
        self.client.login(username=username, password=password)

        response = self.client.get(f'/contentbox/{self.contentbox1.pk}/edit/')
        self.assertEqual(response.status_code, 200)
