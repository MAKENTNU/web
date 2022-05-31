import json

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import translation

from ..multilingual.data_structures import MultiLingualTextStructure
from ..multilingual.formfields import MultiLingualFormField
from ..multilingual.modelfields import MultiLingualTextField


# Ensure the settings are as expected by the tests below
@override_settings(
    LANGUAGES=(
            ('nb', "Norsk"),
            ('en', "English"),
    ),
    LANGUAGE_CODE='nb')
class TestMultiLingualTextStructure(TestCase):
    """
    Tests for the MultiLingualTextStructure class.
    """

    def test_constructor_serialized_json(self):
        """
        Tests if the constructor handles JSON correctly. That is, set the the content of each language to the value
        given in the serialized json.
        """
        content = json.dumps({
            "nb": "test-nb",
            "en": "test-en",
        })
        structure = MultiLingualTextStructure(content, use_default_for_empty=True)
        self.assertEqual(structure["nb"], "test-nb")
        self.assertEqual(structure["en"], "test-en")

    def test_constructor_string(self):
        """
        Tests if the constructor handles corrupt data (i.e. a string) correctly. That is, set the content of the
        default language to this string.
        """
        structure = MultiLingualTextStructure("test-nb", use_default_for_empty=True)
        self.assertEqual(structure["nb"], "test-nb")
        self.assertEqual(structure["en"], "test-nb")

    def test_constructor_None(self):
        """
        Tests if the constructor handles the ``None`` value correctly. That is, the same as if the structure is empty.
        """
        structure = MultiLingualTextStructure(None, use_default_for_empty=True)
        self.assertEqual(structure["nb"], "")
        self.assertEqual(structure["en"], "")

    def test_str(self):
        """
        Tests the ``__str__()`` method. It should return the value of the current language of the thread.
        """
        previous_language = translation.get_language()
        content = json.dumps({
            "nb": "test-nb",
            "en": "test-en",
        })
        structure = MultiLingualTextStructure(content, use_default_for_empty=True)

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
        structure = MultiLingualTextStructure(content, use_default_for_empty=True)

        self.assertEqual(structure["nb"], "test-nb")
        self.assertEqual(structure["en"], "test-en")
        structure["nb"] = "changed-nb"
        self.assertEqual(structure["nb"], "changed-nb")
        self.assertEqual(structure["en"], "test-en")


class TestMultiLingualTextField(TestCase):
    """
    Tests for the ``MultiLingualTextField`` class. Most tests assume that the ``MultiLingualTextStructure`` class
    works correctly.
    """

    def test_to_python(self):
        """
        Tests the ``to_python()`` method. It should return ``None`` (if ``None`` given), the object if ``MultiLingualTextStructure``,
        or the object converted to ``MultiLingualTextStructure`` otherwise.
        """
        field = MultiLingualTextField()
        self.assertEqual(None, field.to_python(None), "to_python of None should always return None.")

        content = json.dumps({
            "nb": "test-nb",
            "en": "test-en",
        })

        structure = MultiLingualTextStructure(content, use_default_for_empty=True)
        self.assertEqual(structure, field.to_python(structure), "to_python of a MultiLingualTextStructure object should"
                                                                " return the object. As this is already the correct "
                                                                "representation.")

        result_from_string = field.to_python(content)
        self.assertEqual(MultiLingualTextStructure, type(result_from_string),
                         "to_python of a string should return the respective MultiLingualTextStructure object.")
        self.assertEqual("test-nb", result_from_string["nb"])
        self.assertEqual("test-en", result_from_string["en"])

    def test_get_prep_value(self):
        """
        Tests the ``get_prep_value()`` method. This should return ``None`` (if ``None`` given), serialized json of its content if
        ``MultiLingualTextStructure`` is given, or just the value otherwise.
        """
        field = MultiLingualTextField()
        self.assertEqual(None, field.get_prep_value(None), "get_prep_value of None should always return None.")

        content = {
            "nb": "test-nb",
            "en": "test-en",
        }
        structure = MultiLingualTextStructure(json.dumps(content), use_default_for_empty=True)
        self.assertEqual(content, json.loads(field.get_prep_value(structure)),
                         "get_prep_value of a MultiLingualTextStructure should return serialized json of its content.")

        self.assertEqual("test", field.get_prep_value("test"),
                         "get_prep_value should not do anything with other object types.")

    def test_get_prep_value_does_not_escape_non_ascii_characters(self):
        # Demonstration of the earlier bug:
        failure_demo_value = json.dumps({"nb": "Abc å"})
        success_demo_value = json.dumps({"nb": "Abc å"}, ensure_ascii=False)
        self.assertNotIn("å", failure_demo_value)
        self.assertIn("å", success_demo_value)
        self.assertEqual(failure_demo_value, r'{"nb": "Abc \u00e5"}')

        field = MultiLingualTextField()
        content = {
            "nb": "Test æøå",
            "en": "Test ???",
        }
        structure = MultiLingualTextStructure(json.dumps(content), use_default_for_empty=False)
        self.assertIn('"nb": "Test æøå"', field.get_prep_value(structure))

    def test_from_db_value(self):
        """
        Tests the ``from_db_value()`` method. Which should always return a ``MultiLingualTextStructure``.
        """
        field = MultiLingualTextField()

        result_none = field.from_db_value(None, None, None)
        self.assertEqual(MultiLingualTextStructure, type(result_none),
                         "from_db_value should always be of type MultiLingualTextStructure")
        self.assertEqual(str(result_none), "")

        result_string = field.from_db_value("test", None, None)
        self.assertEqual(MultiLingualTextStructure, type(result_string),
                         "from_db_value should always be of type MultiLingualTextStructure")
        self.assertEqual(str(result_string), "test")

        content = json.dumps({
            "nb": "test-nb",
            "en": "test-en",
        })
        result_json = field.from_db_value(content, None, None)
        self.assertEqual(MultiLingualTextStructure, type(result_json),
                         "from_db_value should always be of type MultiLingualTextStructure")
        self.assertEqual(result_json["nb"], "test-nb")
        self.assertEqual(result_json["en"], "test-en")


class TestMultiLingualFormField(TestCase):
    """
    Tests for the ``MultiLingualFormField`` class. Tests assume that the ``MultiLingualTextStructure`` class works correctly.
    """

    def setUp(self):
        self.original_languages = settings.LANGUAGES
        # Want to set languages as their order defines the order in which the fields will be given
        settings.LANGUAGES = (
            ("en", "English"),
            ("nb", "Norsk"),
        )

    def tearDown(self):
        settings.LANGUAGES = self.original_languages

    def test_compress(self):
        """
        Tests the ``compress()`` method. We can assume that the data passed is valid data, as the data is cleaned for each
        individual field before being passed to the method.
        """
        form_field = MultiLingualFormField()
        compressed_data = form_field.compress(["test-en", "test-nb"])
        self.assertEqual(MultiLingualTextStructure, type(compressed_data))
        self.assertEqual(compressed_data["nb"], "test-nb")
        self.assertEqual(compressed_data["en"], "test-en")
