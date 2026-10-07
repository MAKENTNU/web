import re
import string
from unittest import TestCase

from util.html_utils import ESCAPE_UNICODE_TO_HTML5, escape_to_named_characters


class Test(TestCase):
    def test_unicode_to_html_5_contains_named_characters_of_correct_format(self):
        named_character_regex = re.compile(r"&[A-Za-z0-9]+;")
        for named_character in ESCAPE_UNICODE_TO_HTML5.values():
            self.assertRegex(named_character, named_character_regex)

    def test_escape_to_named_characters_returns_expected_values(self):
        unicode_to_expected_values = {
            "a": "a",
            "\n": "\n",
            # Printable characters should remain unescaped
            string.printable: string.printable,
            "æøå": "&aelig;&oslash;&aring;",
            "ÆØÅ": "&AElig;&Oslash;&Aring;",
            # From https://no.wikipedia.org/w/index.php?title=Diakritisk_tegn&oldid=21691316
            "Ä, Á, É, È, Ô, Ö og Ü": (
                "&Auml;, &Aacute;, &Eacute;, &Egrave;, &Ocirc;, &Ouml; og &Uuml;"
            ),
            "ä, á, é, è, ô, ö og ü": (
                "&auml;, &aacute;, &eacute;, &egrave;, &ocirc;, &ouml; og &uuml;"
            ),
        }
        for unicode_str, expected_value in unicode_to_expected_values.items():
            self.assertEqual(escape_to_named_characters(unicode_str), expected_value)
