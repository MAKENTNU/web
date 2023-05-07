from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from users.models import User
from util.test_utils import Get, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs
from ..models import Content, Page


# Makes sure that the subdomain of all requests is `docs`
DOCS_CLIENT_DEFAULTS = {'SERVER_NAME': f'docs.{settings.PARENT_HOST}'}


class UrlTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user("user1")
        now = timezone.localtime()
        self.page1 = Page.objects.create(
            title="Page 1",
            created_by=self.user1,
        )
        self.content1 = Content.objects.create(
            page=self.page1,
            last_modified=now - timedelta(days=1),
            content="Lorem ipsum dolor sit amet",
        )
        self.content2 = Content.objects.create(
            page=self.page1,
            last_modified=now,
            content="LoReM iPsUm DoLoR sIt aMeT",
            made_by=self.user1,
        )

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(self.reverse('home'), public=False),
            Get(self.reverse('documentation_page_detail', self.page1.pk), public=False),
            Get(self.reverse('documentation_page_history_detail', self.page1.pk), public=False),
            Get(self.reverse('documentation_page_content_detail', self.page1.pk, self.content1.pk), public=False),
            Get(self.reverse('documentation_page_content_detail', self.page1.pk, self.content2.pk), public=False),
            Get(self.reverse('documentation_page_create'), public=False),
            Get(self.reverse('documentation_page_update', self.page1.pk), public=False),
            Get(self.reverse('documentation_page_search'), public=False),
            Get(f"{self.reverse('documentation_page_search')}?query=lorem", public=False),
            Get(f"{self.reverse('documentation_page_search')}?query=lorem&page=2", public=False),
            Get('/robots.txt', public=True, translated=False),
            Get('/.well-known/security.txt', public=True, translated=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'docs')

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Content, [self.content1, self.content2])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Page, [self.page1])
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')

    @staticmethod
    def reverse(viewname: str, *args):
        return reverse(viewname, args=args, host='docs')
