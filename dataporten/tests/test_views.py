import uuid

from django.contrib.auth import get_user
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from social_django.models import UserSocialAuth

from users.models import User
from util.test_utils import mock_module_attrs
from .. import views
from ..social import DataportenOAuth2


def mock_complete(*args, **kwargs):
    return "mock response"


ldap_data_return_value = {
    'username': "",
}


def mock_get_user_details_from_email(*args, **kwargs):
    return ldap_data_return_value


class ViewTestCase(TestCase):

    def test_logout(self):
        username = 'TEST_USER'
        password = 'TEST_PASS'
        self.user = User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)
        self.assertTrue(get_user(self.client).is_authenticated)
        self.client.post(reverse('logout'))
        self.assertFalse(get_user(self.client).is_authenticated)

    @mock_module_attrs({
        (views, 'complete'): mock_complete,
        (views, 'get_user_details_from_email'): mock_get_user_details_from_email,
    })
    def test_login_wrapper(self):
        user1 = self.create_social_user(
            "user1", "email1", ("", ""), ldap_full_name="", social_data_fullname="Name Nameson",
        )
        ldap_data_return_value['username'] = user1.username

        def assert_original_user1_values():
            self.assert_expected_values_after_login(
                user1, expected_username="user1", expected_full_name="Name Nameson", expected_ldap_full_name="Name Nameson",
            )

        fixed_num_queries = 1  # number of queries that are always executed (currently only `user.social_auth`)
        with self.assertNumQueries(2 + fixed_num_queries):
            assert_original_user1_values()
        # All combinations of missing name fields should result in the same values
        user1.first_name, user1.last_name = "", ""
        user1.save()
        with self.assertNumQueries(1 + fixed_num_queries):
            assert_original_user1_values()
        user1.ldap_full_name = ""
        user1.save()
        with self.assertNumQueries(1 + fixed_num_queries):
            assert_original_user1_values()

        # Changing first_name or last_name should prevent updating any of them on login
        user1.first_name = "New Name"
        user1.save()
        with self.assertNumQueries(0 + fixed_num_queries):
            self.assert_expected_values_after_login(
                user1, expected_username="user1", expected_full_name="New Name Nameson", expected_ldap_full_name="Name Nameson",
            )

        # When the user's full name and ldap_full_name are equal, they should both be set to social_data['fullname']
        user2 = self.create_social_user(
            "user2", "email2", ("Name", "Nameson"), ldap_full_name="Name Nameson", social_data_fullname="New LDAP Name",
        )
        ldap_data_return_value['username'] = user2.username
        with self.assertNumQueries(2 + fixed_num_queries):
            self.assert_expected_values_after_login(
                user2, expected_username="user2", expected_full_name="New LDAP Name", expected_ldap_full_name="New LDAP Name",
            )

        user3 = self.create_social_user(
            "user3", "email3", ("Name", "Nameson"), ldap_full_name="Name Nameson", social_data_fullname="Name Nameson",
        )
        # When the user's username differs from the LDAP data's username, the former should change to match
        ldap_data_return_value['username'] = "ldap_username3"
        self.assert_expected_values_after_login(
            user3, expected_username="ldap_username3", expected_full_name="Name Nameson", expected_ldap_full_name="Name Nameson",
        )
        # When the user's username differs from the local-part of the email (and the LDAP data doesn't contain anything),
        # the username should change to match
        ldap_data_return_value.pop('username')
        self.assert_expected_values_after_login(
            user3, expected_username="email3", expected_full_name="Name Nameson", expected_ldap_full_name="Name Nameson",
        )

    @staticmethod
    def create_social_user(username, email_username, first_and_last_name: tuple[str, str],
                           *, ldap_full_name, social_data_fullname):
        first_name, last_name = first_and_last_name
        user = User.objects.create_user(
            username=username, email=f"{email_username}@example.com",
            first_name=first_name, last_name=last_name, ldap_full_name=ldap_full_name,
        )
        UserSocialAuth.objects.create(user=user, extra_data={'fullname': social_data_fullname}, uid=uuid.uuid4())
        return user

    def assert_expected_values_after_login(self, user, *, expected_username, expected_full_name, expected_ldap_full_name):
        request = HttpRequest()
        request.user = user
        response = views.login_wrapper(request, None)
        self.assertEqual(response, mock_complete())
        self.assertEqual(user.username, expected_username)
        self.assertEqual(user.get_full_name(), expected_full_name)
        self.assertEqual(user.ldap_full_name, expected_ldap_full_name)


class DataportenTestCase(TestCase):

    def test_dataporten(self):
        oa = DataportenOAuth2(None)
        try:
            oa.refresh_token()
        except NotImplementedError:
            pass
