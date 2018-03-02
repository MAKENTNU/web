from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from dataporten.social import DataportenOAuth2


class ViewTestCase(TestCase):
    def test_logout(self):
        username = 'TEST_USER'
        password = 'TEST_PASS'
        self.user = User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)
        self.assertTrue(get_user(self.client).is_authenticated)
        self.client.get(reverse('logout'))
        self.assertFalse(get_user(self.client).is_authenticated)


class DataportenTestCase(TestCase):
    def test_dataporten(self):
        oa = DataportenOAuth2(None)
        try:
            oa.refresh_token()
        except NotImplementedError:
            pass
