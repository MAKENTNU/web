from django.test import SimpleTestCase

from ..templatetags.html_tags import anchor_tag, urlize_target_blank


# noinspection HttpUrlsUsage
class HtmlTagTests(SimpleTestCase):
    def test__urlize_target_blank__returns_expected_html(self):
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

    def test__anchor_tag__returns_expected_html(self):
        self.assertHTMLEqual(anchor_tag("", ""), '<a target="_blank" href=""></a>')
        self.assertHTMLEqual(anchor_tag("", "", target_blank=False), '<a href=""></a>')
        self.assertHTMLEqual(
            anchor_tag("asdf", "asdf"), '<a target="_blank" href="asdf">asdf</a>'
        )
        self.assertHTMLEqual(
            anchor_tag("asdf", "asdf", target_blank=False), '<a href="asdf">asdf</a>'
        )
        self.assertHTMLEqual(
            anchor_tag("example.com", "example.com"),
            '<a target="_blank" href="example.com">example.com</a>',
        )
        self.assertHTMLEqual(
            anchor_tag("https://example.com/", "example.com"),
            '<a target="_blank" href="https://example.com/">example.com</a>',
        )
        self.assertHTMLEqual(
            anchor_tag("mailto:dev@makentnu.no", "dev@makentnu.no"),
            '<a target="_blank" href="mailto:dev@makentnu.no">dev@makentnu.no</a>',
        )
