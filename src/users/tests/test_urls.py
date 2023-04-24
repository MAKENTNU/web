from django.test import TestCase
from django_hosts import reverse

from util.test_utils import Get, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs
from ..models import User


class UrlTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user("user1")
        self.user2 = User.objects.create_user("user2", email="user2@makentnu.no")
        self.user3 = User.objects.create_user("user3", password="1234")
        self.user4 = User.objects.create_user("user4", first_name="Name", last_name="Nameson")
        self.user5 = User.objects.create_user("user5", is_superuser=True, is_staff=True)
        self.user6 = User.objects.create_user("user6", ldap_full_name="Qwer Asdf Zxcv")
        self.user7 = User.objects.create_user("user7", card_number="0123456789")
        # I.e. with all attributes returned by `ldap_utils._get_user_details_from_user_field()`
        self.user_with_basic_info = User.objects.create_user("user8", email="user8@makentnu.no", first_name="Aaa", last_name="Bbb")
        self.users = (self.user1, self.user2, self.user3, self.user4, self.user5, self.user6, self.user7)

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            # adminapipatterns
            Get(reverse('admin_api_basic_user_info', args=[self.user1.username]), public=False),
            Get(reverse('admin_api_basic_user_info', args=[self.user_with_basic_info.username]), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            Get(admin_url, public=False)
            for admin_url in generate_all_admin_urls_for_model_and_objs(User, self.users)
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
