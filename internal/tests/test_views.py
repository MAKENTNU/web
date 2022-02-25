from http import HTTPStatus

from django.templatetags.static import static
from django.test import Client, TestCase

from contentbox.forms import EditSourceContentBoxForm
from contentbox.models import ContentBox
from users.models import User
from util.auth_utils import get_perms
from web.multilingual.data_structures import MultiLingualTextStructure
from .test_urls import INTERNAL_CLIENT_DEFAULTS, reverse_internal


class InternalContentBoxTests(TestCase):

    def setUp(self):
        internal_user = User.objects.create_user("internal_user")
        internal_admin = User.objects.create_user("internal_admin")
        internal_base_perms = ('internal.is_internal', 'contentbox.change_contentbox')
        internal_admin_perms = ('contentbox.change_internal_contentbox', 'internal.can_change_rich_text_source')
        internal_user.add_perms(*internal_base_perms)
        internal_admin.add_perms(*internal_base_perms, *internal_admin_perms)

        self.internal_user_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_admin_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.internal_user_client.force_login(internal_user)
        self.internal_admin_client.force_login(internal_admin)

        self.home_url = reverse_internal('home')
        # Creates the content box by requesting it
        self.internal_user_client.get(self.home_url)
        self.home_content_box = ContentBox.objects.get(title='home')
        # Add these extra change perms (mainly `internal.can_change_rich_text_source`),
        # so that the content box uses the form that allows editing the HTML source code
        self.home_content_box.extra_change_permissions.add(*get_perms(*internal_admin_perms))
        self.home_edit_url = reverse_internal('contentbox_edit', pk=self.home_content_box.pk)

    def test_internal_content_boxes_can_only_be_edited_with_required_permission(self):
        self.assertGreaterEqual(self.internal_user_client.get(self.home_edit_url).status_code, 400)
        self.assertEqual(self.internal_admin_client.get(self.home_edit_url).status_code, HTTPStatus.OK)

    def test_internal_content_boxes_only_contain_edit_buttons_when_user_has_required_permission(self):
        home_content_box_edit_path = f"/contentbox/{self.home_content_box.pk}/edit/"

        def assert_edit_button_in_response(should_button_be_present: bool, client: Client):
            response_html = client.get(self.home_url).content.decode()
            self.assertInHTML('<i class="ui edit icon">', response_html, count=1 if should_button_be_present else 0)
            self.assertEqual(home_content_box_edit_path in response_html, should_button_be_present)

        assert_edit_button_in_response(False, self.internal_user_client)
        assert_edit_button_in_response(True, self.internal_admin_client)

    def test_home_content_box_allows_editing_source(self):
        response = self.internal_admin_client.get(self.home_edit_url)
        self.assertIsInstance(response.context['form'], EditSourceContentBoxForm)
        self.assertInHTML(
            f"""<script src="{static('ckeditor/ckeditor/config_from_django.js')}"
                        data-should-allow-all-tags="true"
                        id="config-from-django">
            </script>""", response.content.decode(), count=1)
        # `editsource` is the name of the toolbar section containing the edit source button (see `CKEDITOR_CONFIGS` in the settings)
        self.assertContains(response, "&quot;editsource&quot;", count=len(MultiLingualTextStructure.SUPPORTED_LANGUAGES))
