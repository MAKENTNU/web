from django.contrib.auth.models import Group
from django.test import TestCase

from users.models import User
from ..auth_utils import get_perm
from ..templatetags.permission_tags import can_view_admin_panel, has_any_permissions_for


class PermissionTagTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="test")
        self.group = Group.objects.create(name="test")
        self.user.groups.add(self.group)

    def clear_user_perm_cache(self):
        # Re-fetch the user from the database, to clear the permission cache (`refresh_from_db()` does not work for this)
        self.user = User.objects.get(pk=self.user.pk)

    def test__has_any_permissions_for__returns_as_expected(self):
        def assert_has_any_permissions_for_group(expected_result: bool):
            # Try all valid model argument variants
            for arg in (Group, 'auth.group', 'group', 'Group'):
                with self.subTest(arg=arg):
                    self.clear_user_perm_cache()
                    self.assertEqual(has_any_permissions_for(self.user, arg), expected_result)

        assert_has_any_permissions_for_group(False)
        self.group.permissions.set([get_perm('auth.add_group')])
        assert_has_any_permissions_for_group(True)
        self.group.permissions.set([get_perm('auth.change_group')])
        assert_has_any_permissions_for_group(True)
        self.group.permissions.set([get_perm('auth.delete_group')])
        assert_has_any_permissions_for_group(True)
        # A view permission should fail the assertion
        self.group.permissions.set([get_perm('auth.view_group')])
        assert_has_any_permissions_for_group(False)
        # Clear the group's permissions
        self.group.permissions.set([])
        assert_has_any_permissions_for_group(False)

    def test__can_view_admin_panel__returns_as_expected(self):
        def assert_can_view_admin_panel(expected_result: bool):
            self.clear_user_perm_cache()
            self.assertEqual(can_view_admin_panel(self.user), expected_result)

        assert_can_view_admin_panel(False)
        self.group.permissions.set([get_perm('news.add_article')])
        assert_can_view_admin_panel(True)
        # A view permission should fail the assertion
        self.group.permissions.set([get_perm('news.view_article')])
        assert_can_view_admin_panel(False)
        # The `Group` model is not shown in the admin panel
        self.group.permissions.set([get_perm('auth.add_group')])
        assert_can_view_admin_panel(False)
        self.group.permissions.set([get_perm('groups.add_committee')])
        assert_can_view_admin_panel(True)
        # This custom permission should pass the assertion, as it's listed in `AdminPanelView.EXTRA_PERMS`
        self.group.permissions.set([get_perm('make_queue.can_create_event_reservation')])
        assert_can_view_admin_panel(True)
        # This custom permission should fail the assertion, as it's not listed in `AdminPanelView.EXTRA_PERMS`
        self.group.permissions.set([get_perm('internal.is_internal')])
        assert_can_view_admin_panel(False)
        # Clear the group's permissions
        self.group.permissions.set([])
        assert_can_view_admin_panel(False)
