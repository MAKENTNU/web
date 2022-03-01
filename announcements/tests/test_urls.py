from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from util.test_utils import Get, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs
from ..models import Announcement


class UrlTests(TestCase):

    def setUp(self):
        now = timezone.localtime()
        self.announcement1 = Announcement.objects.create(
            classification=Announcement.Type.INFO,
            site_wide=True,
            content="Lorem ipsum dolor sit amet",
            link="https://makentnu.no/",
            display_from=now,
        )

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('announcement_admin'), public=False),
            Get(reverse('create_announcement'), public=False),
            Get(reverse('edit_announcement', kwargs={'pk': self.announcement1.pk}), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            Get(admin_url, public=False)
            for admin_url in generate_all_admin_urls_for_model_and_objs(Announcement, [self.announcement1])
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
