from django.test import TestCase
from django_hosts import reverse

from util.test_utils import assert_requesting_paths_succeeds


class UrlTests(TestCase):

    def test_all_get_request_paths_succeed(self):
        paths_to_must_be_authenticated = {
            '/': False,
            reverse('profile'): True,
            reverse('suggest'): True,
        }
        assert_requesting_paths_succeeds(self, paths_to_must_be_authenticated)
