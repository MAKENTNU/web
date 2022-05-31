from http import HTTPStatus
from urllib.parse import urlparse

from django.conf import settings
from django.templatetags.static import static
from django.test import Client, TestCase, override_settings
from django.urls import clear_url_caches

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
        self.home_content_box = ContentBox.objects.get(url_name='home')
        # Add these extra change perms (mainly `internal.can_change_rich_text_source`),
        # so that the content box uses the form that allows editing the HTML source code
        self.home_content_box.extra_change_permissions.add(*get_perms(*internal_admin_perms))
        self.home_edit_url = reverse_internal('contentbox_edit', self.home_content_box.pk)

        self.internal_content_boxes = (self.home_content_box,)

    @classmethod
    def tearDownClass(cls):
        # Clear the cache again, after filling it with URLs prefixed with `/en`
        # when testing with the `LANGUAGE_CODE` setting set to `en` below
        clear_url_caches()

    def test_internal_content_boxes_can_only_be_edited_with_required_permission(self):
        self.assertEqual(self.internal_user_client.get(self.home_edit_url).status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(self.internal_admin_client.get(self.home_edit_url).status_code, HTTPStatus.OK)

    def test_internal_content_boxes_only_contain_visible_edit_buttons_when_user_has_required_permission(self):
        home_content_box_edit_path = f"/contentbox/{self.home_content_box.pk}/edit/"

        def assert_visible_edit_button_in_response(should_button_be_present: bool, client: Client):
            response_html = client.get(self.home_url).content.decode()
            self.assertEqual("hidden edit-button" in response_html, not should_button_be_present)
            self.assertEqual(home_content_box_edit_path in response_html, should_button_be_present)

        assert_visible_edit_button_in_response(False, self.internal_user_client)
        assert_visible_edit_button_in_response(True, self.internal_admin_client)

    def test_home_content_box_allows_editing_source(self):
        response = self.internal_admin_client.get(self.home_edit_url)
        self.assertIsInstance(response.context['form'], EditSourceContentBoxForm)
        self.assertInHTML(
            f"""<script src="{static('ckeditor/ckeditor/config_from_django.js')}"
                        data-should-allow-all-tags="true"
                        id="config-from-django">
            </script>""", response.content.decode(), count=1)
        # `editsource` is the name of the toolbar section containing the edit source button (see `CKEDITOR_CONFIGS` in the settings)
        self.assertContains(response, "&quot;editsource&quot;",
                            # This view only uses one language, and so there should only be one occurrence of this string
                            count=1)

    @override_settings(LANGUAGE_CODE='nb')
    def test_internal_content_boxes_accept_posting_just_norwegian(self):
        self._test_internal_content_boxes_accept_posting_just_one_language()

    @override_settings(LANGUAGE_CODE='en')
    def test_internal_content_boxes_accept_posting_just_english(self):
        # Have to clear the cached URLs, to make calls to `reverse()` return paths that are not prefixed with `/en`
        # (after having overridden the `LANGUAGE_CODE` setting so that it's set to `en`)
        clear_url_caches()
        self._test_internal_content_boxes_accept_posting_just_one_language()

    def _test_internal_content_boxes_accept_posting_just_one_language(self):
        mock_content = "asdf"
        expected_content_languages = {
            language: mock_content for language in MultiLingualTextStructure.SUPPORTED_LANGUAGES
        }

        for content_box in self.internal_content_boxes:
            with self.subTest(content_box=content_box):
                edit_url = reverse_internal('contentbox_edit', content_box.pk)
                response = self.internal_admin_client.post(edit_url, {
                    f'title_{settings.LANGUAGE_CODE}': "Mock Title",
                    f'content_{settings.LANGUAGE_CODE}': mock_content,
                })
                display_url = reverse_internal(content_box.url_name)
                # `display_url` contains a relative scheme and a host, so only compare the paths
                self.assertRedirects(response, urlparse(display_url).path)
                content_box.refresh_from_db()
                content_text_structure: MultiLingualTextStructure = content_box.content
                # The content box should contain the same content for all languages
                self.assertEqual(len(content_text_structure.languages), len(expected_content_languages))
                for language in expected_content_languages:
                    self.assertEqual(content_text_structure[language], expected_content_languages[language])
