from http import HTTPStatus
from urllib.parse import urlparse

from django.conf import settings
from django.test import Client, TestCase
from django.utils import translation
from django_hosts import reverse

from news.tests.test_urls import NewsTestBase
from users.models import User
from util.test_utils import Get, assert_requesting_paths_succeeds


# Makes sure that the subdomain of all requests is `admin`
ADMIN_CLIENT_DEFAULTS = {'SERVER_NAME': f'admin.{settings.PARENT_HOST}'}


def reverse_admin(viewname: str, args=None, **kwargs):
    return reverse(f'admin:{viewname}', args=args, kwargs=kwargs, host='admin')


class UrlTests(NewsTestBase, TestCase):

    def setUp(self):
        username = "TEST_USER"
        password = "TEST_PASS"
        self.user = User.objects.create_user(username=username, password=password)

        self.anon_client = Client()
        self.user_client = Client()
        self.user_client.login(username=username, password=password)

        # Populate the front page
        self.init_objs()

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
            Get(reverse_admin('index'), public=False),
            Get(reverse_admin('password_change'), public=False),
            *[
                Get(reverse_admin('app_list', args=[app_label]), public=False)
                for app_label in ['announcements', 'auth', 'checkin', 'contentbox', 'docs', 'faq', 'groups', 'internal', 'make_queue', 'makerspace',
                                  'news', 'social_django', 'users']
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')

    def test_all_old_urls_succeed(self):
        path_predicates = [
            Get('/rules/', public=True, redirect=True),
            Get('/reservation/rules/1/', public=True, redirect=True),
            Get('/reservation/rules/usage/1/', public=True, redirect=True),

            Get(f'/news/article/{self.article1.pk}/', public=True, redirect=True),
            Get(f'/news/event/{self.event1.pk}/', public=True, redirect=True),
            Get(f'/news/ticket/{self.ticket1.pk}/', public=False, redirect=True),
            Get(f'/news/ticket/me/', public=False, redirect=True),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_setting_language_does_not_require_any_permissions(self):
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

    def test_ckeditor_uploader_urls_are_found_on_all_subdomains(self):
        upload_path = urlparse(reverse('ckeditor_upload')).path
        browse_path = urlparse(reverse('ckeditor_browse')).path
        ckeditor_paths = (upload_path, browse_path)

        for subdomain, expected_urlconf in (
                ('', 'web.urls'),
                ('i', 'internal.urls'),
                ('admin', 'web.admin_urls'),
                ('docs', 'docs.urls'),
        ):
            if subdomain:
                client = Client(SERVER_NAME=f'{subdomain}.{settings.PARENT_HOST}')
            else:
                client = self.client

            for path in ckeditor_paths:
                with self.subTest(subdomain=subdomain, path=path):
                    response = client.get(upload_path)
                    # A redirect (to the login page) status code implies that the path exists
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertEqual(response.wsgi_request.urlconf, expected_urlconf)
