from http import HTTPStatus
from urllib.parse import urlparse

from django.conf import settings
from django.test import Client, TestCase
from django.utils import translation
from django_hosts import reverse

from contentbox.models import ContentBox
from make_queue.models.machine import Machine
from news.tests.test_urls import NewsTestBase
from users.models import User
from util.test_utils import Get, assert_requesting_paths_succeeds
from util.url_utils import reverse_admin


# Makes sure that the subdomain of all requests is `admin`
ADMIN_CLIENT_DEFAULTS = {'SERVER_NAME': f'admin.{settings.PARENT_HOST}'}


class UrlTests(NewsTestBase, TestCase):

    def setUp(self):
        username = "TEST_USER"
        password = "TEST_PASS"
        self.user = User.objects.create_user(username=username, password=password)

        self.anon_client = Client()
        self.user_client = Client()
        self.user_client.login(username=username, password=password)

        self.about_content_box = ContentBox.objects.create(url_name='about')
        self.content_box1 = ContentBox.objects.create(url_name='content_box1')
        self.content_box2 = ContentBox.objects.create(url_name='content_box2')
        self.content_boxes = (self.about_content_box, self.content_box1, self.content_box2)

        # Populate the front page
        self.init_objs()

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            # urlpatterns
            Get('/robots.txt', public=True, translated=False),
            Get('/.well-known/security.txt', public=True, translated=False),
            # ckeditor_uploader_urls()
            Get(reverse('ckeditor_browse'), public=False, translated=False),

            # admin_urlpatterns
            Get(reverse('admin_panel'), public=False),

            # content_box_urlpatterns
            *[
                Get(reverse('content_box_update', args=[content_box.pk]), public=False)
                for content_box in self.content_boxes
            ],

            # about_urlpatterns
            Get(reverse('about'), public=True),
            Get(reverse('contact'), public=True),

            # urlpatterns
            Get(reverse('index_page'), public=True),
            Get(reverse('apply'), public=True),
            Get('/søk/', public=True),
            Get('/sok/', public=True),
            Get(reverse('cookies'), public=True),
            Get(reverse('privacypolicy'), public=True),
            Get(reverse('javascript_catalog'), public=True),
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
                for app_label in [
                    # The apps are listed in order of appearance on the admin index page,
                    # which is controlled by `web.admin.WebAdminSite`
                    'constance',

                    'users',
                    'groups',
                    'contentbox',
                    'announcements',
                    'news',
                    'make_queue',
                    'makerspace',
                    'faq',

                    'internal',
                    'docs',

                    'checkin',
                    'auth',

                    'social_django',
                ]
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')

    def test_all_old_urls_succeed(self):
        machine1 = Machine.objects.create(name="Machine 1", machine_type_id=1)

        path_predicates = [
            Get('/rules/', public=True, redirect=True),

            Get('/reservation/', public=True, redirect=True),
            Get(f'/reservation/2023/16/{machine1.pk}/', public=True, redirect=True),

            Get('/reservation/me/', public=False, redirect=True),
            Get('/reservation/admin/', public=False, redirect=True),
            Get('/reservation/slots/', public=False, redirect=True),

            Get('/reservation/rules/1/', public=True, redirect=True),
            Get('/reservation/machinetypes/1/rules/', public=True, redirect=True),
            Get('/reservation/rules/usage/1/', public=True, redirect=True),
            Get('/reservation/machinetypes/1/rules/usage/', public=True, redirect=True),

            Get(f'/news/article/{self.article1.pk}/', public=True, redirect=True),
            Get(f'/news/event/{self.event1.pk}/', public=True, redirect=True),
            Get(f'/news/ticket/{self.ticket1.pk}/', public=False, redirect=True),
            Get('/news/ticket/me/', public=False, redirect=True),
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
