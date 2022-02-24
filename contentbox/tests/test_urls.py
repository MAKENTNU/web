import importlib
from typing import Callable, List, Tuple
from urllib.parse import urlparse

from django.test import Client, TestCase
from django.urls import URLPattern, URLResolver
from django_hosts import reverse

from internal.tests.test_urls import INTERNAL_CLIENT_DEFAULTS, reverse_internal
from users.models import User
from util.auth_utils import get_perm
from web.hosts import host_patterns
from web.multilingual.data_structures import MultiLingualTextStructure
from ..models import ContentBox
from ..views import DisplayContentBoxView


class UrlTests(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_user("superuser", is_superuser=True, is_staff=True)

        self.main_client = Client()
        self.internal_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.url__client__should_be_bleached__tuples = (
            (reverse('about'), self.main_client, True),
            (reverse('contact'), self.main_client, True),
            (reverse('apply'), self.main_client, True),
            (reverse('cookies'), self.main_client, True),
            (reverse('privacypolicy'), self.main_client, True),

            (reverse('makerspace'), self.main_client, True),
            (reverse('rules'), self.main_client, True),

            (reverse_internal('home'), self.internal_client, False),
        )

    def test_content_box_url_count_is_as_expected(self):
        all_content_box_url_patterns = self.get_all_content_box_url_patterns()
        self.assertEqual(
            len(all_content_box_url_patterns),
            len(self.url__client__should_be_bleached__tuples)
            # + `/søk/` and `/sok/`
            + 2,
        )

    # Code based on https://stackoverflow.com/a/19162337
    @staticmethod
    def get_all_content_box_url_patterns() -> List[URLPattern]:
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
                if view_class and issubclass(view_class, DisplayContentBoxView):
                    patterns.append(pattern)

        for host in host_patterns:
            module = importlib.import_module(host.urlconf)
            check_urls(module.urlpatterns)

        return patterns

    def test_form_input_is_properly_bleached(self):
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
                """
                    <a href="https://makentnu.dev" target="_blank" name="link" download>LINK</a>
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

        for url, client, should_be_bleached in self.url__client__should_be_bleached__tuples:
            with self.subTest(url=url):
                client.force_login(self.superuser)
                response = client.get(url)
                content_box: ContentBox = response.context['object']
                if not should_be_bleached:
                    # Add the permission that is expected for non-bleached content boxes to have
                    content_box.extra_change_permissions.add(get_perm('internal.can_change_rich_text_source'))

                self.assert_content_is_bleached_expectedly_when_posted(original_content__bleached_content__tuples, should_be_bleached, url,
                                                                       content_box, client)

    def assert_content_is_bleached_expectedly_when_posted(self, original_content__bleached_content__tuples: List[Tuple[str, str]],
                                                          should_be_bleached: bool, url: str, content_box: ContentBox, client: Client):
        change_url = reverse('contentbox_edit', args=[content_box.pk])
        for original_content, bleached_content in original_content__bleached_content__tuples:
            response = client.post(change_url, {
                # `content_0` etc. are the expected names of the subfields (one for each language) of `MultiLingualFormField`
                f'content_{i}': original_content for i in range(len(MultiLingualTextStructure.SUPPORTED_LANGUAGES))
            })
            # `url` contains a relative scheme and a host, so only compare the paths
            self.assertRedirects(response, urlparse(url).path)
            content_box.refresh_from_db()
            content_text_structure: MultiLingualTextStructure = content_box.content

            # Check that the content has been bleached expectedly
            expected_content = bleached_content if should_be_bleached else original_content
            for content in content_text_structure.languages.values():
                self.assertHTMLEqual(content, expected_content)
