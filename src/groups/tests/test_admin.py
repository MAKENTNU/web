from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase

from users.models import User
from util.test_utils import set_without_duplicates
from web.tests.test_urls import ADMIN_CLIENT_DEFAULTS, reverse_admin
from ..admin import InheritanceGroupAdmin
from ..models import InheritanceGroup


class InheritanceGroupAdminTestCase(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user("admin", is_staff=True, is_superuser=True)
        self.admin_client = Client(**ADMIN_CLIENT_DEFAULTS)
        self.admin_client.force_login(self.admin)

        self.org = InheritanceGroup.objects.create(name='Org')
        self.mentor = InheritanceGroup.objects.create(name='Mentor')
        self.dev = InheritanceGroup.objects.create(name='Dev')
        self.event = InheritanceGroup.objects.create(name='Event')
        self.chairperson = InheritanceGroup.objects.create(name='Leder')

        self.mentor.parents.add(self.org)
        self.dev.parents.add(self.org)
        self.event.parents.add(self.org)
        self.chairperson.parents.add(self.mentor, self.dev, self.event)

        self.org_perms = {
            Permission.objects.create(codename='perm1', name="Perm 1", content_type=ContentType.objects.get_for_model(InheritanceGroup))
        }
        self.org.own_permissions.add(*self.org_perms)

        self.admin_add_url = reverse_admin('groups_inheritancegroup_add')
        self.admin_change_dev_url = reverse_admin('groups_inheritancegroup_change', args=[self.dev.pk])

    def test_form_contains_expected_fields_and_related_field_querysets(self):
        response = self.admin_client.get(self.admin_add_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        form = response.context['adminform']
        expected_fields = ['name', 'parents', 'own_permissions']
        self.assertListEqual(list(form.fields), expected_fields)
        self.assertSetEqual(
            set_without_duplicates(self, form.fields['parents'].queryset),
            set(InheritanceGroup.objects.all()),
        )

        response = self.admin_client.get(self.admin_change_dev_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        form = response.context['adminform']
        self.assertListEqual(list(form.fields), expected_fields)
        self.assertSetEqual(
            set_without_duplicates(self, form.fields['parents'].queryset),
            set(self.dev.get_available_parents()),
        )

    def test_get_inherited_permissions_contains_expected_permissions(self):
        response = self.admin_client.get(self.admin_change_dev_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        admin: InheritanceGroupAdmin = response.context['adminform'].model_admin

        permissions_string = admin.get_inherited_permissions(self.dev)
        permissions = set_without_duplicates(self, permissions_string.splitlines())
        self.assertSetEqual(permissions, {str(perm) for perm in self.org_perms})
