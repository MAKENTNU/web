from django.contrib.auth.models import Permission
from users.models import User
from django.test import TestCase

from .models import ContentBox
from .views import DisplayContentBoxView


class ModelTestCase(TestCase):

    def test_str(self):
        contentbox = ContentBox.objects.create(title='TEST_TITLE')
        self.assertEqual(contentbox.title, 'TEST_TITLE')
        self.assertEqual(contentbox.title, str(contentbox))

    def test_display_view(self):
        view = DisplayContentBoxView()
        view.title = 'TEST_TITLE'
        context = view.get_context_data()
        self.assertTrue('contentbox' in context)
        self.assertEqual(context['contentbox'].title, 'TEST_TITLE')

    def test_edit_without_permission(self):
        ContentBox.objects.get_or_create(title='TEST_TITLE')
        response = self.client.get('/contentbox/1/edit/')
        self.assertNotEqual(response.status_code, 200)

    def test_edit_with_permission(self):
        username = 'TEST_USER'
        password = 'TEST_PASS'
        user = User.objects.create_user(username=username, password=password)
        permission = Permission.objects.get(codename='change_contentbox')
        user.user_permissions.add(permission)
        self.client.login(username=username, password=password)
        ContentBox.objects.get_or_create(title='TEST_TITLE')
        response = self.client.get('/contentbox/1/edit/')
        self.assertEqual(response.status_code, 200)
