from typing import Set
from urllib.parse import urlparse

from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django_hosts import reverse

from users.models import User
from .models import Member, SystemAccess, GuidanceHours

from internal.forms import EditGuidanceHoursForm
import datetime
from django.forms import model_to_dict
from django.core import serializers

from unittest import skip
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
from http import HTTPStatus
from internal.templatetags import guidance_hours


ADMIN_CLIENT_DEFAULTS = {'SERVER_NAME': 'admin.testserver'}
class GuidanceHoursUpdateMemberTest(TestCase):
    def setUp(self):
        self.password = "TEST_PASS"
        self.admin_user = User.objects.create_user(username="ADMIN", password=self.password, is_staff=True, is_superuser=True)
        self.user = User.objects.create_user(username="USER", password=self.password)
        self.member = Member.objects.create(user=self.admin_user)
        self.non_member = User.objects.create_user(username='NON_MEMBER', password=self.password)
        permission = Permission.objects.get(codename='is_internal')
        reset_permission = Permission.objects.get(codename='can_change_guidancehours')
        self.user.user_permissions.add(permission)
        self.admin_user.user_permissions.add(permission)

        self.member_client = Client(**ADMIN_CLIENT_DEFAULTS)
        self.member_client.login(username=self.admin_user, password=self.password)
        self.member_with_guidance_exemption = Member.objects.create(user=self.user, guidance_exemption=True)

        day = 'Monday'
        start_time = datetime.time(hour=14)
        end_time = datetime.time(hour=16, minute=15)
        self.member = Client()
        self.monday_slot = GuidanceHours.objects.create(day=day, start_time=start_time, end_time=end_time)


    def test_update_end_time(self):
        change_url = reverse('admin:%s_%s_change' % (self.monday_slot._meta.app_label, self.monday_slot.__class__.__name__.lower()), args=[self.monday_slot.pk], host="admin")
        data = model_to_dict(self.monday_slot, exclude=['id', 'slot_one', 'slot_two', 'slot_three', 'slot_four'])
        hour_changed = 17
        data['end_time'] = datetime.time(hour=hour_changed)

        response = self.member_client.post(
            change_url,
            data
        )
        self.monday_slot.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(self.monday_slot.end_time, datetime.time(hour=hour_changed))

    def test_end_time_before_start_time(self):
        INVALID_END_TIME = GuidanceHours.objects.create(
            day='Tuesday',
            start_time=datetime.time(hour=12),
            end_time=datetime.time(hour=10)
        )

        self.assertRaises(ValidationError, INVALID_END_TIME.clean)

    def test_valid_form_data_is_valid(self):
        valid_form_data = {
            'slot_one': '',
            'slot_two': '',
            'slot_three': '',
            'slot_four': ''
        }

        VALID_EMPTY_FORM = EditGuidanceHoursForm(data=valid_form_data)
        self.assertTrue(VALID_EMPTY_FORM.is_valid())

        valid_form_data['slot_one'] = self.member
        FORM_WITH_VALID_MEMBER = EditGuidanceHoursForm(data=valid_form_data)
        self.assertTrue(FORM_WITH_VALID_MEMBER)

    def test_add_non_member(self):

        form_data = {
            'slot_one': self.non_member,
            'slot_two': '',
            'slot_three': '',
            'slot_four': ''
        }

        form = EditGuidanceHoursForm(data=form_data)
        self.assertFalse(form.is_valid())


    @skip('Not implemented')
    def test_add_member_with_guidance_exemption(self):
        form_data = {
            'slot_one': self.member_with_guidance_exemption,
            'slot_two': '',
            'slot_three': '',
            'slot_four': ''
        }

        form = EditGuidanceHoursForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_get_sorted_slots_by_earliest_start_time(self):
        pass


    def test_reset_guidance_hours_table(self):
        pass

    
    def test_successful_response_guidance_hours_view(self):
        pass

class UrlTests(TestCase):

    def setUp(self):
        password = "TEST_PASS"
        non_member_user = User.objects.create_user(username="NON_MEMBER", password=password)
        member_user = User.objects.create_user(username="MEMBER", password=password)
        member_editor_user = User.objects.create_user(username="MEMBER_EDITOR", password=password)

        self.add_permissions(member_user, "is_internal")
        self.add_permissions(member_editor_user, "is_internal",
                             "can_register_new_member", "can_edit_group_membership", "change_systemaccess")
        self.member = Member.objects.create(user=member_user)
        self.member_editor = Member.objects.create(user=member_editor_user)

        self.anon_client = Client()
        self.non_member_client = Client()
        self.member_client = Client()
        self.member_editor_client = Client()

        self.all_clients = {self.anon_client, self.non_member_client, self.member_client, self.member_editor_client}

        self.non_member_client.login(username=non_member_user, password=password)
        self.member_client.login(username=member_user, password=password)
        self.member_editor_client.login(username=member_editor_user, password=password)

    @staticmethod
    def add_permissions(user: User, *codenames: str):
        for codename in codenames:
            permission = Permission.objects.get(codename=codename)
            user.user_permissions.add(permission)

    @staticmethod
    def get_url(name: str, args=None):
        return reverse(name, args, host="internal", host_args=["internal"])

    def _test_url_permissions(self, url: str, allowed_clients: Set[Client]):
        disallowed_clients = self.all_clients - allowed_clients
        for client in disallowed_clients:
            self.assertNotEqual(client.get(url, follow=True).status_code, 200)
        for client in allowed_clients:
            self.assertEqual(client.get(url, follow=True).status_code, 200)

    def _test_internal_url(self, url: str):
        self._test_url_permissions(url, {self.member_client, self.member_editor_client})

    def _test_editor_url(self, url: str):
        self._test_url_permissions(url, {self.member_editor_client})

    def _test_internal_post_url(self, url: str, data: dict, *, expected_redirect_url: str):
        # Unauthorized users should be redirected to login
        response = self.anon_client.post(url, data)
        self.assertTrue(urlparse(response.url).path.startswith("/login"))
        response = self.non_member_client.post(url, data)
        self.assertTrue(urlparse(response.url).path.startswith("/login"))

        self.assertRedirects(self.member_client.post(url, data), expected_redirect_url)
        self.assertRedirects(self.member_editor_client.post(url, data), expected_redirect_url)

    @override_settings(DEFAULT_HOST="internal")
    def test_permissions(self):
        self._test_internal_url(self.get_url("members"))
        self._test_internal_url(self.get_url("members", [self.member.pk]))
        self._test_editor_url(self.get_url("add-member"))

        # All members can edit themselves, but only editors can edit other members
        self._test_url_permissions(self.get_url("edit-member", [self.member.pk]),
                                   allowed_clients={self.member_client, self.member_editor_client})
        self._test_url_permissions(self.get_url("edit-member", [self.member_editor.pk]),
                                   allowed_clients={self.member_editor_client})

        self._test_editor_url(self.get_url("member-quit", [self.member.pk]))
        self._test_editor_url(self.get_url("member-undo-quit", [self.member.pk]))
        self._test_editor_url(self.get_url("member-retire", [self.member.pk]))
        self._test_editor_url(self.get_url("member-undo-retire", [self.member.pk]))

        for system_access in self.member.systemaccess_set.all():
            # No one is allowed to change their "website" access. Other than that,
            # all members can edit their own accesses, but only editors can edit other members'.
            allowed_clients = {self.member_client, self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
            self._test_url_permissions(self.get_url("toggle-system-access", [system_access.pk]),
                                       allowed_clients=allowed_clients)

        for system_access in self.member_editor.systemaccess_set.all():
            # No one is allowed to change their "website" access
            allowed_clients = {self.member_editor_client} if system_access.name != SystemAccess.WEBSITE else set()
            self._test_url_permissions(self.get_url("toggle-system-access", [system_access.pk]),
                                       allowed_clients=allowed_clients)

        self._test_internal_url(self.get_url("home"))

        self._test_internal_post_url(self.get_url("set_language"), {"language": "en"}, expected_redirect_url="/en/")
        self._test_internal_post_url(self.get_url("set_language"), {"language": "nb"}, expected_redirect_url="/")
