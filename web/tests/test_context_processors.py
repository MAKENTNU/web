from django.test import TestCase, override_settings
from django_hosts import reverse


class CommonContextVariablesTests(TestCase):

    @override_settings(LANGUAGE_CODE='nb')
    def test_common_context_variables_have_expected_values_when_norwegian(self):
        self.assert_common_context_variables_have_expected_values('nb')

    @override_settings(LANGUAGE_CODE='en')
    def test_common_context_variables_have_expected_values_when_english(self):
        self.assert_common_context_variables_have_expected_values('en')

    def assert_common_context_variables_have_expected_values(self, default_language_code: str):
        context = self.client.get("/").context
        self.assertEqual(context['DEFAULT_LANGUAGE_CODE'], default_language_code)
        self.assertEqual(context['CURRENT_LANGUAGE_CODE'], default_language_code)
        self.assertEqual(context['USES_DATAPORTEN_AUTH'], False)


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
        # Should work regardless of the path, as non-existent paths return a 404 page with the same context variables
        response = self.client.get("/about/")
        login_redirect_path = self.get_login_redirect_path(response)
        self.assertEqual(login_redirect_path, "/about/")

    @staticmethod
    def get_login_redirect_path(response):
        return response.context['login_next_param'].split("?next=")[-1]
