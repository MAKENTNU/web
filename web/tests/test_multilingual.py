import json
from django.test import TestCase
from django.utils import translation

from web import settings
from web.multilingual.data_structures import MultiLingualTextStructure
from web.multilingual.database import MultiLingualTextField


class TestMultiLingualTextStructure(TestCase):
    """
    Tests for the MultiLingualTextStructure class
    """

    def setUp(self):
        self.original_languages = settings.LANGUAGES
        self.original_language_code = settings.LANGUAGE_CODE
        settings.LANGUAGES = (
            ("nb", "Norsk"),
            ("en", "English"),
        )
        settings.LANGUAGE_CODE = "nb"

    def tearDown(self):
        settings.LANGUAGES = self.original_languages
        settings.LANGUAGE_CODE = self.original_language_code

    def test_constructor_serialized_json(self):
        """
        Tests if the constructor handles JSON correctly. That is, set the the content of each language to the value
        given in the serialized json
        """
        content = json.dumps({
            "nb": "test-nb",
            "en": "test-en",
        })
        structure = MultiLingualTextStructure(content, True)
        self.assertEqual(structure["nb"], "test-nb")
        self.assertEqual(structure["en"], "test-en")

    def test_constructor_string(self):
        """
        Tests if the constructor handles corrupt data (i.e. a string) correctly. That is, set the content of the
        default language to this string
        """
        structure = MultiLingualTextStructure("test-nb", True)
        self.assertEqual(structure["nb"], "test-nb")
        self.assertEqual(structure["en"], "test-nb")

    def test_constructor_None(self):
        """
        Tests if the constructor handles the none value correctly. That is the same as if the structure is empty
        """
        structure = MultiLingualTextStructure(None, True)
        self.assertEqual(structure["nb"], "")
        self.assertEqual(structure["en"], "")

    def test_str(self):
        """
        Tests the to string method. It should return the value of the current language of the thread
        """
        previous_language = translation.get_language()
        content = json.dumps({
            "nb": "test-nb",
            "en": "test-en",
        })
        structure = MultiLingualTextStructure(content, True)

        translation.activate("nb")
        self.assertEqual(str(structure), "test-nb")

        translation.activate("en")
        self.assertEqual(str(structure), "test-en")

        translation.activate(previous_language)

    def test_set_item(self):
        """
        Tests if the builtin set item function is correctly overwritten, so that we can set the value of a language in
        the array syntax way.
        """
        content = json.dumps({
            "nb": "test-nb",
            "en": "test-en",
        })
        structure = MultiLingualTextStructure(content, True)

        self.assertEqual(structure["nb"], "test-nb")
        self.assertEqual(structure["en"], "test-en")
        structure["nb"] = "changed-nb"
        self.assertEqual(structure["nb"], "changed-nb")
        self.assertEqual(structure["en"], "test-en")
