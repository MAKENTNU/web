from django.test import TestCase
from django_hosts import reverse


class TestLoginRedirect(TestCase):

    def test_front_page_has_no_next_parameter(self):
        response = self.client.get("/")
        self.assertEqual(response.context['login_next_param'], "")

    def test_login_page_keeps_redirect_target(self):
        login_path = reverse('login', host='main')
        response = self.client.get(f"{login_path}?next=/asdf/")
        login_redirect_path = self.get_login_redirect_path(response)
        self.assertEqual(login_redirect_path, "/asdf/")

    def test_other_page_redirects_back(self):
        # Should work regardless of the path, as non-existant paths return a 404 page with the same context variables
        response = self.client.get("/about/")
        login_redirect_path = self.get_login_redirect_path(response)
        self.assertEqual(login_redirect_path, "/about/")

    @staticmethod
    def get_login_redirect_path(response):
        return response.context['login_next_param'].split("?next=")[-1]
