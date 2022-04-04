from django.test import TestCase

from ..templatetags.html_tags import urlize_target_blank


class HtmlTagTests(TestCase):

    def test_urlize_target_blank_returns_expected_html(self):
        urls_to_expected_html = {
            "": "",
            "asdf": "asdf",
            None: "None",
            123: "123",
            "dev@makentnu.no": '<a target="_blank" href="mailto:dev@makentnu.no">dev@makentnu.no</a>',
            "example.com": '<a target="_blank" href="http://example.com" rel="nofollow">example.com</a>',
            "example.com/?a=1&b=2": '<a target="_blank" href="http://example.com/?a=1&b=2" rel="nofollow">example.com/?a=1&b=2</a>',
            "https://example.com/": '<a target="_blank" href="https://example.com/" rel="nofollow">https://example.com/</a>',
            "https://example.com?a=1&b=2": '<a target="_blank" href="https://example.com?a=1&b=2" rel="nofollow">https://example.com?a=1&b=2</a>',
        }
        for url, expected_html in urls_to_expected_html.items():
            self.assertHTMLEqual(urlize_target_blank(url), expected_html)
