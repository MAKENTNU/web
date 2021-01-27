from django.test import Client, TestCase

from contentbox.models import ContentBox
from users.models import User
from .test_urls import INTERNAL_CLIENT_DEFAULTS, reverse_internal


class InternalContentBoxTests(TestCase):

    def setUp(self):
        internal_user = User.objects.create_user("internal_user")
        internal_admin = User.objects.create_user("internal_admin")
        internal_user.add_perms('internal.is_internal', 'contentbox.change_contentbox')
        internal_admin.add_perms('internal.is_internal', 'contentbox.change_contentbox', 'contentbox.change_internal_contentbox')

        self.internal_user_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_admin_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_user_client.force_login(internal_user)
        self.internal_admin_client.force_login(internal_admin)

        self.home_url = reverse_internal('home')
        # Creates the content box by requesting it
        self.internal_user_client.get(self.home_url)
        self.home_content_box = ContentBox.objects.get(title='home')
        self.home_edit_url = reverse_internal('contentbox_edit', pk=self.home_content_box.pk)

    def test_internal_content_boxes_can_only_be_edited_with_required_permission(self):
        self.assertGreaterEqual(self.internal_user_client.get(self.home_edit_url).status_code, 400)
        self.assertEqual(self.internal_admin_client.get(self.home_edit_url).status_code, 200)

    def test_internal_content_boxes_only_contain_edit_buttons_when_user_has_required_permission(self):
        home_content_box_edit_path = f"/contentbox/{self.home_content_box.pk}/edit/"

        def assert_edit_button_in_response(should_button_be_present: bool, client: Client):
            response_html = client.get(self.home_url).content.decode()
            self.assertInHTML('<i class="edit icon">', response_html, count=1 if should_button_be_present else 0)
            self.assertEqual(home_content_box_edit_path in response_html, should_button_be_present)

        assert_edit_button_in_response(False, self.internal_user_client)
        assert_edit_button_in_response(True, self.internal_admin_client)
