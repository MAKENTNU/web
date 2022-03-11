from django.contrib.auth.models import Group
from django.test import TestCase
from django_hosts import reverse

from util.test_utils import (
    CleanUpTempFilesTestMixin, Get, MOCK_JPG_FILE, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs,
)
from ..models import Committee, InheritanceGroup


class UrlTests(CleanUpTempFilesTestMixin, TestCase):

    def setUp(self):
        self.group1 = InheritanceGroup.objects.create(name="Group 1")
        self.committee1 = Committee.objects.create(
            group=self.group1,
            description="Lorem ipsum dolor sit amet",
            email="committee1@makentnu.no",
            image=MOCK_JPG_FILE,
            clickbait="Wow!",
        )

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('committee_list'), public=True),
            Get(reverse('committee_detail', kwargs={'pk': self.committee1.pk}), public=True),
            Get(reverse('committee_edit', kwargs={'pk': self.committee1.pk}), public=False),
            Get(reverse('committee_admin'), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Group, [self.group1.group_ptr])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(InheritanceGroup, [self.group1])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Committee, [self.committee1])
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
