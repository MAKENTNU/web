from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from news.models import Article
from .admin import InheritanceGroupAdmin
from .models import InheritanceGroup as Group, Committee


def permission_to_perm(permission):
    """Find the <app_label>.<codename> string for a permission object"""
    return '.'.join([permission.content_type.app_label, permission.codename])


class MockRequest:
    pass


class MockSuperUser:
    def has_perm(self, *args, **kwargs):
        return True


class PermGroupTestCase(TestCase):
    def setUp(self):
        org = Group.objects.create(name='Org')
        mentor = Group.objects.create(name='Mentor')
        mentor.parents.add(org)
        dev = Group.objects.create(name='Dev')
        dev.parents.add(org)
        arr = Group.objects.create(name='Arrangement')
        arr.parents.add(org)
        Group.objects.create(name='Leder').parents.add(mentor, dev, arr)

        content_type = ContentType.objects.get_for_model(Article)
        for i in range(5):
            Permission.objects.create(
                codename=f'perm{i}',
                name=f'Perm {i}',
                content_type=content_type,
            )

    def test_update_single_parent(self):
        org = Group.objects.get(name='Org')
        dev = Group.objects.get(name='Dev')
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
        org = Group.objects.get(name='Org')
        dev = Group.objects.get(name='Dev')
        mentor = Group.objects.get(name='Mentor')
        leder = Group.objects.get(name='Leder')

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
        org = Group.objects.get(name='Org')
        dev = Group.objects.get(name='Dev')
        perm1 = Permission.objects.get(codename='perm1')
        perm2 = Permission.objects.get(codename='perm2')

        org.own_permissions.add(perm1)
        dev.own_permissions.add(perm2)

        new_group = Group.objects.create(name='new-group')
        new_group.parents.add(dev)

        self.assertIn(perm1, new_group.permissions.all())
        self.assertIn(perm2, new_group.permissions.all())

    def test_user(self):
        user_model = get_user_model()

        org = Group.objects.get(name='Org')
        dev = Group.objects.get(name='Dev')
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

    def test_get_sub_group(self):
        org = Group.objects.get(name='Org')
        arr = Group.objects.get(name='Arrangement')
        dev = Group.objects.get(name='Dev')
        web = Group.objects.create(name='Web')
        web.parents.add(dev)

        self.assertIn(dev, org.get_sub_groups())
        self.assertIn(arr, org.get_sub_groups())
        self.assertIn(web, org.get_sub_groups())
        self.assertIn(web, dev.get_sub_groups())
        self.assertNotIn(arr, dev.get_sub_groups())
        self.assertNotIn(dev, arr.get_sub_groups())

    def test_get_all_parents(self):
        org = Group.objects.get(name='Org')
        arr = Group.objects.get(name='Arrangement')
        dev = Group.objects.get(name='Dev')
        web = Group.objects.create(name='Web')
        web.parents.add(dev)

        self.assertIn(dev, web.get_all_parents())
        self.assertIn(org, web.get_all_parents())
        self.assertNotIn(arr, web.get_all_parents())
        self.assertNotIn(web, arr.get_all_parents())

    def test_get_available_parents(self):
        org = Group.objects.get(name='Org')
        arr = Group.objects.get(name='Arrangement')
        mentor = Group.objects.get(name='Mentor')
        dev = Group.objects.get(name='Dev')
        web = Group.objects.create(name='Web')
        web.parents.add(dev)
        misc = Group.objects.create(name='Misc')

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
        dev = Group.objects.get(name='Dev')
        permissions = dev.permissions.all()
        own_permissions = dev.own_permissions.all()
        inherited_permissions = dev.inherited_permissions
        for perm in permissions:
            if perm in own_permissions:
                self.assertNotIn(perm, inherited_permissions)
            else:
                self.assertIn(perm, inherited_permissions)


class InheritanceGroupAdminTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.request = MockRequest()
        self.request.user = MockSuperUser()
        org = Group.objects.create(name='Org')
        mentor = Group.objects.create(name='Mentor')
        mentor.parents.add(org)
        dev = Group.objects.create(name='Dev')
        dev.parents.add(org)
        arr = Group.objects.create(name='Arrangement')
        arr.parents.add(org)
        Group.objects.create(name='Leder').parents.add(mentor, dev, arr)

    def test_get_form(self):
        admin = InheritanceGroupAdmin(Group, self.site)
        expected_fields = ['name', 'parents', 'own_permissions']
        form = admin.get_form(self.request)
        self.assertEqual(list(form.base_fields), expected_fields)

        expected_parents = Group.objects.all()
        self.assertEqual(set(form.base_fields['parents'].queryset), set(expected_parents))

        form = admin.get_form(self.request, obj=Group.objects.get(name='Dev'))
        expected_parents = Group.objects.get(name='Dev').get_available_parents()
        self.assertEqual(set(form.base_fields['parents'].queryset), set(expected_parents))

    def test_inherited_permissions(self):
        admin = InheritanceGroupAdmin(Group, self.site)
        dev = Group.objects.get(name='Dev')
        permissions = set(admin.inherited_permissions(dev))
        for perm in dev.inherited_permissions:
            self.assertIn(str(perm), permissions)


class CommitteeTestCase(TestCase):
    def setUp(self):
        org = Group.objects.create(name='Org')
        mentor = Group.objects.create(name='Mentor')
        mentor.parents.add(org)
        dev = Group.objects.create(name='Dev')
        dev.parents.add(org)
        arr = Group.objects.create(name='Arrangement')
        arr.parents.add(org)
        Group.objects.create(name='Leder').parents.add(mentor, dev, arr)

    def test_name(self):
        dev = Committee.objects.create(
            group=Group.objects.get(name='Dev'),
            description='Website and stuff',
            email='dev@makentnu.no',
        )
        self.assertEqual(dev.name, 'Dev')
        self.assertEqual(str(dev), 'Dev')
