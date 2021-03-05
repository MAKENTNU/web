from django.contrib.auth.models import Group
from django.test import TestCase

from users.models import User
from ..auth_utils import get_perm
from ..templatetags.permission_tags import has_any_permissions


class HasAnyPermissionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="test")

    def test_no_permissions(self):
        self.assertFalse(has_any_permissions(self.user))

    def test_has_user_permission(self):
        self.user.add_perms('auth.add_group')
        self.assertTrue(has_any_permissions(self.user))

    def test_has_group_permission(self):
        group = Group.objects.create(name="test")
        self.user.groups.add(group)
        group.permissions.add(get_perm('auth.add_group'))
        self.assertTrue(has_any_permissions(self.user))
