from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.test import TestCase

from web.templatetags.permission_tags import has_any_permissions


class HasAnyPermissionTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="test")

    def test_no_permissions(self):
        self.assertFalse(has_any_permissions(self.user))

    def test_has_user_permission(self):
        self.user.user_permissions.add(Permission.objects.get(name="Can add group"))
        self.assertTrue(has_any_permissions(self.user))

    def test_has_group_permission(self):
        group = Group.objects.create(name="test")
        self.user.groups.add(group)
        group.permissions.add(Permission.objects.get(name="Can add group"))
        self.assertTrue(has_any_permissions(self.user))
