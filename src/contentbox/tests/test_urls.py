import importlib
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from http import HTTPStatus
from typing import Protocol
from urllib.parse import urlparse

from django.test import Client, TestCase
from django.urls import URLPattern, URLResolver
from django_hosts import reverse

from docs.tests.test_urls import DOCS_CLIENT_DEFAULTS
from internal.tests.test_urls import INTERNAL_CLIENT_DEFAULTS, reverse_internal
from users.models import User
from util.auth_utils import get_perm
from util.test_utils import Get, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs
from web.hosts import host_patterns
from web.multilingual.data_structures import MultiLingualTextStructure
from web.multilingual.widgets import MultiLingualTextEdit
from web.tests.test_urls import ADMIN_CLIENT_DEFAULTS
from ..models import ContentBox
from ..views import ContentBoxDetailView


class ReverseCallable(Protocol):
    def __call__(self, viewname: str, *args) -> str: ...


@dataclass
class ContentBoxAssertionStruct:
    reverse_func: ReverseCallable
    viewname: str
    client: Client
    should_be_bleached: bool = field(kw_only=True)

    @cached_property
    def url(self) -> str:
        return self.reverse_func(self.viewname)


def reverse_main(viewname: str, *args):
    return reverse(viewname, args=args)


class UrlTests(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_user("superuser", is_superuser=True, is_staff=True)

        self.main_client = Client()
        self.internal_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        admin_client = Client(**ADMIN_CLIENT_DEFAULTS)
        docs_client = Client(**DOCS_CLIENT_DEFAULTS)
        self.all_clients = (
            self.main_client, self.internal_client, admin_client, docs_client,
        )

        self.content_box_assertion_structs = (
            ContentBoxAssertionStruct(reverse_main, 'about', self.main_client, should_be_bleached=True),
            ContentBoxAssertionStruct(reverse_main, 'contact', self.main_client, should_be_bleached=True),
            ContentBoxAssertionStruct(reverse_main, 'apply', self.main_client, should_be_bleached=True),
            ContentBoxAssertionStruct(reverse_main, 'cookies', self.main_client, should_be_bleached=True),
            ContentBoxAssertionStruct(reverse_main, 'privacypolicy', self.main_client, should_be_bleached=True),

            ContentBoxAssertionStruct(reverse_main, 'makerspace', self.main_client, should_be_bleached=True),
            ContentBoxAssertionStruct(reverse_main, 'rules', self.main_client, should_be_bleached=True),

            ContentBoxAssertionStruct(reverse_internal, 'home', self.internal_client, should_be_bleached=False),
            ContentBoxAssertionStruct(reverse_internal, 'dev-board', self.internal_client, should_be_bleached=False),
            ContentBoxAssertionStruct(reverse_internal, 'event-board', self.internal_client, should_be_bleached=True),
            ContentBoxAssertionStruct(reverse_internal, 'mentor-board', self.internal_client, should_be_bleached=True),
            ContentBoxAssertionStruct(reverse_internal, 'pr-board', self.internal_client, should_be_bleached=True),

            ContentBoxAssertionStruct(reverse_internal, 'make-history', self.internal_client, should_be_bleached=True),
        )

    def get_content_box_from_url(self, url: str, client: Client) -> ContentBox:
        client.force_login(self.superuser)
        response = client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        return response.context['object']

    def test_content_box_url_count_is_as_expected(self):
        all_content_box_url_patterns = self.get_all_content_box_url_patterns()
        self.assertEqual(
            len(all_content_box_url_patterns),
            len(self.content_box_assertion_structs)
            # + `/søk/` and `/sok/`
            + 2,
        )

    # Code based on https://stackoverflow.com/a/19162337
    @staticmethod
    def get_all_content_box_url_patterns() -> list[URLPattern]:
        patterns = []

        def check_urls(urlpatterns, prefix=''):
            for pattern in urlpatterns:
                # If the pattern includes other patterns (using the `include()` method):
                if isinstance(pattern, URLResolver):
                    new_prefix = prefix
                    if pattern.namespace:
                        new_prefix = prefix + (':' if prefix else '') + pattern.namespace
                    check_urls(pattern.url_patterns, prefix=new_prefix)
                    continue

                pattern: URLPattern
                view_class = getattr(pattern.callback, 'view_class', None)
                if view_class and issubclass(view_class, ContentBoxDetailView):
                    patterns.append(pattern)

        for host in host_patterns:
            module = importlib.import_module(host.urlconf)
            check_urls(module.urlpatterns)

        return patterns

    def test_all_admin_get_request_paths_succeed(self):
        content_boxes = [
            self.get_content_box_from_url(struct.url, struct.client)
            for struct in self.content_box_assertion_structs
        ]
        path_predicates = [
            Get(admin_url, public=False)
            for admin_url in generate_all_admin_urls_for_model_and_objs(ContentBox, content_boxes)
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')

    def test_change_pages_can_only_be_reached_on_the_same_subdomain_as_the_display_pages(self):
        for client in self.all_clients:
            client.force_login(self.superuser)

        for struct in self.content_box_assertion_structs:
            content_box: ContentBox = struct.client.get(struct.url).context['object']
            for client in self.all_clients:
                with self.subTest(struct=struct, client=client):
                    change_url = struct.reverse_func('contentbox_edit', content_box.pk)
                    response = client.get(change_url)
                    # Change pages should only be reachable on the same subdomain as the content box' display page is defined on
                    same_subdomain = struct.client == client
                    self.assertEqual(response.status_code, HTTPStatus.OK if same_subdomain else HTTPStatus.NOT_FOUND)

    def test_form_input_is_properly_bleached(self):
        # Facilitates printing the whole diff if the tests fail, which is useful due to the long strings in this test case
        self.maxDiff = None

        def unchanged(s: str):
            return s

        def escaped(s: str):
            return s.replace("<", "&lt;").replace(">", "&gt;")

        original_content__bleached_content__tuples = [
            (
                "".join(f"<{tag}></{tag}>" for tag in [
                    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'div', 'p', 'span', 'pre',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 's', 'sub', 'sup', 'u', 'big', 'small', 'q', 'figure', 'figcaption', 'table',
                ]),
                unchanged,
            ),
            (
                # Attributes with optional values (like `download`) should be assigned to an empty value (like `""`), or the tests might fail
                """
                    <a href="https://makentnu.dev" target="_blank" name="link" download="">LINK</a>
                    <a id="anchor" href="#anchor" name="anchor">Scroll to anchor</a>
                    <a href="mailto:styret@makentnu.no" style="text-decoration: none;"></a>
                    <a href="tel:+47 123 45 678"></a>

                    <div style="text-align: center;">
                        <figure class="image" style="display: inline-block;">
                            <img src="/media/image.jpg" width="100" height="100" alt="An image :)"/>
                            <figcaption>Some caption</figcaption>
                        </figure>
                    </div>

                    <p style="margin-left: 40px; text-align: right;"></p>
                    <p style="text-align: center;">
                        <span style="color: #2ecc71; background-color: #e74c3c;"></span>
                    </p>

                    <br/>
                    <hr/>

                    &lt;script&gt; alert("hey"); &lt;/script&gt;
                """,
                unchanged,
            ),
            (
                """
                    <script> alert("hey"); </script>
                    <style type="text/javascript"> alert("hey"); </style>
                    <script defer src="/static/script.js"></script>

                    <form></form>
                    <input/>

                    <applet></applet>
                    <iframe src="https://calendar.google.com/calendar/embed"></iframe>

                    <html lang="en">
                    <head>
                        <title>Some title</title>
                        <meta charset="UTF-8">
                        <link href="/static/style.css"/>
                    </head>
                    <body></body>
                    </html>

                    <customtagname></customtagname>
                """,
                escaped,
            ),
            (
                """
                    <!-- Comment -->
                """,
                "",
            ),
            (
                # From https://stackoverflow.com/q/29906775
                """
                    <img src="javascript:alert('hey');"/>
                    <img src="java&#010;script:alert('hey');"/>
                    <img src="java&#X0A;script:alert('hey');"/>
                """,
                """
                    <img/>
                    <img/>
                    <img/>
                """,
            ),
            (
                # From https://html5sec.org/#144
                """
                    <a href="javascript:&apos;<svg onload&equals;alert&lpar;1&rpar;&nvgt;&apos;">CLICK</a>
                """,
                """
                    <a>CLICK</a>
                """,
            ),
        ]
        # Replace the functions with their return values, which imitate how the original content will be bleached
        for i, (original_content, bleached_content) in enumerate(original_content__bleached_content__tuples):
            if callable(bleached_content):
                bleach_mock_func: Callable[[str], str] = bleached_content
                original_content__bleached_content__tuples[i] = (original_content, bleach_mock_func(original_content))

        for struct in self.content_box_assertion_structs:
            with self.subTest(url=struct.url):
                content_box = self.get_content_box_from_url(struct.url, struct.client)
                if not struct.should_be_bleached:
                    # Add the permission that is expected for non-bleached content boxes to have
                    content_box.extra_change_permissions.add(get_perm('internal.can_change_rich_text_source'))

                self.assert_content_is_bleached_expectedly_when_posted(original_content__bleached_content__tuples,
                                                                       struct.should_be_bleached, struct.url, content_box, struct.client)

    def assert_content_is_bleached_expectedly_when_posted(self, original_content__bleached_content__tuples: list[tuple[str, str]],
                                                          should_be_bleached: bool, url: str, content_box: ContentBox, client: Client):
        change_url = reverse('contentbox_edit', args=[content_box.pk])
        for original_content, bleached_content in original_content__bleached_content__tuples:
            response = client.post(
                change_url,
                {subwidget_name: subwidget_name.title() for subwidget_name in MultiLingualTextEdit.get_subwidget_names('title')}
                | {subwidget_name: original_content for subwidget_name in MultiLingualTextEdit.get_subwidget_names('content')},
            )
            # `url` contains a relative scheme and a host, so only compare the paths
            self.assertRedirects(response, urlparse(url).path)
            content_box.refresh_from_db()
            content_text_structure: MultiLingualTextStructure = content_box.content

            # Check that the content has been bleached expectedly
            expected_content = bleached_content if should_be_bleached else original_content
            for language in content_text_structure.languages:
                self.assertHTMLEqual(content_text_structure[language], expected_content)
