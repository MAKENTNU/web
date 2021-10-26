from django.test import TestCase
from django_hosts import reverse

from util.test_utils import Get, assert_requesting_paths_succeeds


class UrlTests(TestCase):

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('skills_present_list'), public=True),
            Get(reverse('profile'), public=False),
            Get(reverse('suggest'), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)
