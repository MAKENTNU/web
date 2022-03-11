from django.contrib.auth.models import Group
from django.test import TestCase

from users.models import User
from ..auth_utils import get_perm
from ..templatetags.permission_tags import has_any_permissions, has_any_permissions_for


class HasAnyPermissionsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="test")

    def test_no_permissions(self):
        self.assertFalse(has_any_permissions(self.user))

    def test_has_user_permission(self):
        self.user.add_perms('auth.add_group')
        self.assertTrue(has_any_permissions(self.user))

    def test_has_group_permission(self):
        self.assertFalse(has_any_permissions(self.user))
        self.assertFalse(has_any_permissions_for(self.user, Group))

        group = Group.objects.create(name="test")
        group.permissions.add(get_perm('auth.add_group'))
        self.user.groups.add(group)
        self.clear_user_perm_cache()

        self.assertTrue(has_any_permissions(self.user))
        self.assertTrue(has_any_permissions_for(self.user, Group))

    def clear_user_perm_cache(self):
        # Re-fetch the user from the database, to clear the permission cache (`refresh_from_db()` does not work for this)
        self.user = User.objects.get(pk=self.user.pk)

    def test__has_any_permissions_for__returns_as_expected(self):
        group = Group.objects.create(name="test")
        self.user.groups.add(group)

        def assert_has_any_permissions_for_group(expected_result: bool):
            # Try all valid model argument variants
            for arg in (Group, 'auth.group', 'group', 'Group'):
                with self.subTest(arg=arg):
                    self.clear_user_perm_cache()
                    self.assertEqual(has_any_permissions_for(self.user, arg), expected_result)

        assert_has_any_permissions_for_group(False)
        group.permissions.set([get_perm('auth.add_group')])
        assert_has_any_permissions_for_group(True)
        group.permissions.set([get_perm('auth.change_group')])
        assert_has_any_permissions_for_group(True)
        group.permissions.set([get_perm('auth.delete_group')])
        assert_has_any_permissions_for_group(True)
        # Clear the group's permissions
        group.permissions.set([])
        assert_has_any_permissions_for_group(False)

        # Invalid model arguments should raise an exception
        with self.assertRaises(ValueError):
            has_any_permissions_for(self.user, 1)
        with self.assertRaises(ValueError):
            has_any_permissions_for(self.user, group)
