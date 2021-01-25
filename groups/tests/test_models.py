from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from news.models import Article
from users.models import User
from ..models import Committee, InheritanceGroup


def permission_to_perm(permission):
    """Find the <app_label>.<codename> string for a permission object."""
    return '.'.join([permission.content_type.app_label, permission.codename])


# See the `0008_add_default_inheritancegroups_and_committees.py` migration for which InheritanceGroups are created by default
class PermGroupTestCase(TestCase):

    def setUp(self):
        org = InheritanceGroup.objects.create(name='Org')
        mentor = InheritanceGroup.objects.create(name='Mentor')
        mentor.parents.add(org)
        dev = InheritanceGroup.objects.create(name='Dev')
        dev.parents.add(org)
        arr = InheritanceGroup.objects.create(name='Arrangement')
        arr.parents.add(org)
        InheritanceGroup.objects.create(name='Leder').parents.add(mentor, dev, arr)

        for i in range(5):
            Permission.objects.create(
                codename=f'perm{i}',
                name=f'Perm {i}',
                content_type=ContentType.objects.get_for_model(Article),
            )

    def test_update_single_parent(self):
        org = InheritanceGroup.objects.get(name='Org')
        dev = InheritanceGroup.objects.get(name='Dev')
        perm1 = Permission.objects.get(codename='perm1')

        org.own_permissions.add(perm1)

        self.assertIn(perm1, org.permissions.all())
        self.assertIn(perm1, dev.permissions.all())

        org.own_permissions.remove(perm1)

        self.assertNotIn(perm1, org.permissions.all())
        self.assertNotIn(perm1, dev.permissions.all())

        dev.own_permissions.add(perm1)

        self.assertNotIn(perm1, org.permissions.all())
        self.assertIn(perm1, dev.permissions.all())

        dev.own_permissions.clear()

        self.assertNotIn(perm1, org.permissions.all())
        self.assertNotIn(perm1, dev.permissions.all())

    def test_update_multiple_parents(self):
        org = InheritanceGroup.objects.get(name='Org')
        dev = InheritanceGroup.objects.get(name='Dev')
        mentor = InheritanceGroup.objects.get(name='Mentor')
        leder = InheritanceGroup.objects.get(name='Leder')

        perm1 = Permission.objects.get(codename='perm1')
        perm2 = Permission.objects.get(codename='perm2')
        perm3 = Permission.objects.get(codename='perm3')
        perm4 = Permission.objects.get(codename='perm4')

        org.own_permissions.add(perm1)
        dev.own_permissions.add(perm2)
        mentor.own_permissions.add(perm3)
        leder.own_permissions.add(perm4)

        self.assertIn(perm1, org.permissions.all())
        self.assertIn(perm1, dev.permissions.all())
        self.assertIn(perm1, mentor.permissions.all())
        self.assertIn(perm1, leder.permissions.all())

        self.assertNotIn(perm2, org.permissions.all())
        self.assertIn(perm2, dev.permissions.all())
        self.assertNotIn(perm2, mentor.permissions.all())
        self.assertIn(perm2, leder.permissions.all())

        self.assertNotIn(perm3, org.permissions.all())
        self.assertNotIn(perm3, dev.permissions.all())
        self.assertIn(perm3, mentor.permissions.all())
        self.assertIn(perm3, leder.permissions.all())

        self.assertNotIn(perm4, org.permissions.all())
        self.assertNotIn(perm4, dev.permissions.all())
        self.assertNotIn(perm4, mentor.permissions.all())
        self.assertIn(perm4, leder.permissions.all())

        mentor.own_permissions.remove(perm3)

        self.assertNotIn(perm3, org.permissions.all())
        self.assertNotIn(perm3, dev.permissions.all())
        self.assertNotIn(perm3, mentor.permissions.all())
        self.assertNotIn(perm3, leder.permissions.all())

        org.own_permissions.clear()

        self.assertNotIn(perm1, org.permissions.all())
        self.assertNotIn(perm1, dev.permissions.all())
        self.assertNotIn(perm1, mentor.permissions.all())
        self.assertNotIn(perm1, leder.permissions.all())

    def test_add_group(self):
        org = InheritanceGroup.objects.get(name='Org')
        dev = InheritanceGroup.objects.get(name='Dev')
        perm1 = Permission.objects.get(codename='perm1')
        perm2 = Permission.objects.get(codename='perm2')

        org.own_permissions.add(perm1)
        dev.own_permissions.add(perm2)

        new_group = InheritanceGroup.objects.create(name='new-group')
        new_group.parents.add(dev)

        self.assertIn(perm1, new_group.permissions.all())
        self.assertIn(perm2, new_group.permissions.all())

    def test_user(self):
        user_model = User

        org = InheritanceGroup.objects.get(name='Org')
        dev = InheritanceGroup.objects.get(name='Dev')
        perm1 = Permission.objects.get(codename='perm1')
        perm2 = Permission.objects.get(codename='perm2')
        perm1_str = permission_to_perm(perm1)
        perm2_str = permission_to_perm(perm2)
        org.own_permissions.add(perm1)

        user1 = user_model.objects.create_user('Test1', 'test1@test.com', '1234')
        user2 = user_model.objects.create_user('Test2', 'test2@test.com', '1234')

        user1.groups.add(org)
        user2.groups.add(dev)
        dev.own_permissions.add(perm2)
        self.assertTrue(user1.has_perm(perm1_str))
        self.assertFalse(user1.has_perm(perm2_str))
        self.assertTrue(user2.has_perm(perm1_str))
        self.assertTrue(user2.has_perm(perm2_str))

    def test_get_all_children(self):
        org = InheritanceGroup.objects.get(name='Org')
        arr = InheritanceGroup.objects.get(name='Arrangement')
        dev = InheritanceGroup.objects.get(name='Dev')
        web = InheritanceGroup.objects.create(name='Web')
        web.parents.add(dev)

        self.assertIn(dev, org.get_all_children())
        self.assertIn(arr, org.get_all_children())
        self.assertIn(web, org.get_all_children())
        self.assertIn(web, dev.get_all_children())
        self.assertNotIn(arr, dev.get_all_children())
        self.assertNotIn(dev, arr.get_all_children())

    def test_get_all_parents(self):
        org = InheritanceGroup.objects.get(name='Org')
        arr = InheritanceGroup.objects.get(name='Arrangement')
        dev = InheritanceGroup.objects.get(name='Dev')
        web = InheritanceGroup.objects.create(name='Web')
        web.parents.add(dev)

        self.assertIn(dev, web.get_all_parents())
        self.assertIn(org, web.get_all_parents())
        self.assertNotIn(arr, web.get_all_parents())
        self.assertNotIn(web, arr.get_all_parents())

    def test_get_available_parents(self):
        org = InheritanceGroup.objects.get(name='Org')
        arr = InheritanceGroup.objects.get(name='Arrangement')
        mentor = InheritanceGroup.objects.get(name='Mentor')
        dev = InheritanceGroup.objects.get(name='Dev')
        web = InheritanceGroup.objects.create(name='Web')
        web.parents.add(dev)
        misc = InheritanceGroup.objects.create(name='Misc')

        self.assertEqual(org.get_available_parents().count(), 1)
        self.assertIn(misc, org.get_available_parents().all())

        self.assertEqual(dev.get_available_parents().count(), 4)
        self.assertIn(org, dev.get_available_parents().all())
        self.assertIn(arr, dev.get_available_parents().all())
        self.assertIn(mentor, dev.get_available_parents().all())
        self.assertIn(misc, dev.get_available_parents().all())
        self.assertNotIn(web, dev.get_available_parents().all())

        self.assertEqual(misc.get_available_parents().count(), 6)

    def test_inherited_permissions(self):
        dev = InheritanceGroup.objects.get(name='Dev')
        permissions = dev.permissions.all()
        own_permissions = dev.own_permissions.all()
        inherited_permissions = dev.inherited_permissions
        for perm in permissions:
            if perm in own_permissions:
                self.assertNotIn(perm, inherited_permissions)
            else:
                self.assertIn(perm, inherited_permissions)


# See the `0008_add_default_inheritancegroups_and_committees.py` migration for which Committees are created by default
class CommitteeTestCase(TestCase):

    def setUp(self):
        org = InheritanceGroup.objects.create(name='Org')
        mentor = InheritanceGroup.objects.create(name='Mentor')
        mentor.parents.add(org)
        dev = InheritanceGroup.objects.create(name='Dev')
        dev.parents.add(org)
        arr = InheritanceGroup.objects.create(name='Arrangement')
        arr.parents.add(org)
        InheritanceGroup.objects.create(name='Leder').parents.add(mentor, dev, arr)

    def test_name(self):
        dev = Committee.objects.create(
            group=InheritanceGroup.objects.get(name='Dev'),
            description='Website and stuff',
            email='dev@makentnu.no',
        )
        self.assertEqual(dev.name, 'Dev')
        self.assertEqual(str(dev), 'Dev')
