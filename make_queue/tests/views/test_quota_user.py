from django.contrib.auth.models import User
from django.test import TestCase

from make_queue.tests.utility import template_view_get_context_data
from make_queue.views.quota.user import GetUserQuotaView


class GetUserQuotaViewTest(TestCase):

    def test_context_data(self):
        user = User.objects.create_user(username="Test")
        self.assertEqual(template_view_get_context_data(GetUserQuotaView, user), {"user": user})
