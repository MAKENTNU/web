from django.test import TestCase
from django_hosts import reverse

from makerspace.models import Equipment
from util.test_utils import (
    MOCK_JPG_FILE,
    CleanUpTempFilesTestMixin,
    Get,
    assert_requesting_paths_succeeds,
    generate_all_admin_urls_for_model_and_objs,
)


class UrlTests(CleanUpTempFilesTestMixin, TestCase):
    def setUp(self):
        self.equipment1 = Equipment.objects.create(
            title="Test equipment 1",
            description="Lorem ipsum dolor sit amet",
            image=MOCK_JPG_FILE,
        )

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            # equipment_urlpatterns
            Get(reverse("equipment_list"), public=True),
            Get(reverse("equipment_detail", args=[self.equipment1.pk]), public=True),
            # urlpatterns
            Get(reverse("makerspace"), public=True),
            Get(reverse("rules"), public=True),
            # specific_equipment_adminpatterns
            Get(reverse("equipment_update", args=[self.equipment1.pk]), public=False),
            # equipment_adminpatterns
            Get(reverse("admin_equipment_list"), public=False),
            Get(reverse("equipment_create"), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            Get(admin_url, public=False)
            for admin_url in generate_all_admin_urls_for_model_and_objs(
                Equipment, [self.equipment1]
            )
        ]
        assert_requesting_paths_succeeds(self, path_predicates, "admin")
