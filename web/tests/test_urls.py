from django.conf import settings
from django.test import Client, TestCase
from django.utils import translation
from django_hosts import reverse

from news.tests.test_urls import UrlTests as NewsUrlTests
from users.models import User
from util.test_utils import CleanUpTempFilesTestMixin, Get, assert_requesting_paths_succeeds


# Makes sure that the subdomain of all requests is `admin`
ADMIN_CLIENT_DEFAULTS = {'SERVER_NAME': 'admin.testserver'}


class UrlTests(CleanUpTempFilesTestMixin, TestCase):

    def setUp(self):
        username = "TEST_USER"
        password = "TEST_PASS"
        self.user = User.objects.create_user(username=username, password=password)

        self.anon_client = Client()
        self.user_client = Client()
        self.user_client.login(username=username, password=password)

        # Populate the front page
        NewsUrlTests.init_objs(self)

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get('/robots.txt', public=True, translated=False),
            Get('/.well-known/security.txt', public=True, translated=False),
            Get(reverse('front_page'), public=True),
            Get(reverse('adminpanel'), public=False),
            Get(reverse('about'), public=True),
            Get(reverse('contact'), public=True),
            Get(reverse('apply'), public=True),
            Get('/søk/', public=True),
            Get('/sok/', public=True),
            Get(reverse('cookies'), public=True),
            Get(reverse('privacypolicy'), public=True),
            Get(reverse('ckeditor_browse'), public=False, translated=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            Get('/robots.txt', public=True, translated=False),
            Get('/.well-known/security.txt', public=True, translated=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')

    def test_all_old_urls_succeed(self):
        path_predicates = [
            Get('/rules/', public=True, success_code=301),
            Get('/reservation/rules/1/', public=True, success_code=301),
            Get('/reservation/rules/usage/1/', public=True, success_code=301),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_set_language(self):
        response = self.anon_client.post(reverse('set_language'), {'language': 'en'})
        self.assertRedirects(response, '/en/')
        response = self.anon_client.post(reverse('set_language'), {'language': 'nb'})
        self.assertRedirects(response, '/')

        response = self.user_client.post(reverse('set_language'), {'language': 'en'})
        self.assertRedirects(response, '/en/')
        response = self.user_client.post(reverse('set_language'), {'language': 'nb'})
        self.assertRedirects(response, '/')

        # Previously indirectly caused decorating "set_language" with "permission_required" (see https://github.com/MAKENTNU/web/pull/297).
        # [This test can potentially be removed]
        self.user_client.get(reverse('home', host='internal', host_args=['internal']),
                             HTTP_HOST=f'internal.{settings.PARENT_HOST}')
        # Should not redirect to login (caused by the above line)
        response = self.anon_client.post(reverse('set_language'), {'language': 'en'})
        self.assertRedirects(response, '/en/')

        # Reset current language back to the default
        translation.activate(settings.LANGUAGE_CODE)
