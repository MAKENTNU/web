from django.contrib.auth.models import User
from django.test import TestCase

from make_queue.models import Quota3D, QuotaSewing
from make_queue.templatetags.quota import get_3d_quota, get_sewing_quota


class GetQuotaTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="test")

    def test_get_non_created_quota_3D(self):
        quota = get_3d_quota(self.user)
        self.assertEqual(quota.user, self.user)
        self.assertEqual(quota, Quota3D.objects.get(user=self.user))

    def test_get_non_created_quota_sewing(self):
        quota = get_sewing_quota(self.user)
        self.assertEqual(quota.user, self.user)
        self.assertEqual(quota, QuotaSewing.objects.get(user=self.user))

    def test_created_quota_3D(self):
        user_quota = Quota3D.objects.create(user=self.user)
        retrieved_quota = get_3d_quota(self.user)
        self.assertEqual(user_quota, retrieved_quota)

    def test_created_quota_sewing(self):
        user_quota = Quota3D.objects.create(user=self.user)
        retrieved_quota = get_3d_quota(self.user)
        self.assertEqual(user_quota, retrieved_quota)
