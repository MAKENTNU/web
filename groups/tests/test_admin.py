from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from ..admin import InheritanceGroupAdmin
from ..models import InheritanceGroup


class MockRequest:
    pass


class MockSuperUser:

    def has_perm(self, *args, **kwargs):
        return True


class InheritanceGroupAdminTestCase(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.request = MockRequest()
        self.request.user = MockSuperUser()
        org = InheritanceGroup.objects.create(name='Org')
        mentor = InheritanceGroup.objects.create(name='Mentor')
        mentor.parents.add(org)
        dev = InheritanceGroup.objects.create(name='Dev')
        dev.parents.add(org)
        arr = InheritanceGroup.objects.create(name='Arrangement')
        arr.parents.add(org)
        InheritanceGroup.objects.create(name='Leder').parents.add(mentor, dev, arr)

    def test_get_form(self):
        admin = InheritanceGroupAdmin(InheritanceGroup, self.site)
        expected_fields = ['name', 'parents', 'own_permissions']
        form = admin.get_form(self.request)
        self.assertListEqual(list(form.base_fields), expected_fields)

        expected_parents = InheritanceGroup.objects.all()
        self.assertSetEqual(set(form.base_fields['parents'].queryset), set(expected_parents))

        form = admin.get_form(self.request, obj=InheritanceGroup.objects.get(name='Dev'))
        expected_parents = InheritanceGroup.objects.get(name='Dev').get_available_parents()
        self.assertSetEqual(set(form.base_fields['parents'].queryset), set(expected_parents))

    def test_inherited_permissions(self):
        admin = InheritanceGroupAdmin(InheritanceGroup, self.site)
        dev = InheritanceGroup.objects.get(name='Dev')
        permissions = set(admin.get_inherited_permissions(dev))
        for perm in dev.inherited_permissions:
            self.assertIn(str(perm), permissions)
