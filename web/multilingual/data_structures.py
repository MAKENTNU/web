import json
from json import JSONDecodeError

from django.conf import settings
from django.utils.translation import get_language

from util.logging_utils import get_request_logger


class MultiLingualTextStructure:
    """
    Data structure to keep track of multilingual string data.
    """
    SUPPORTED_LANGUAGES = tuple(lang_code for lang_code, _lang_name in settings.LANGUAGES)

    def __init__(self, json_content: str, *, languages=SUPPORTED_LANGUAGES, use_default_for_empty=True):
        self.use_default_for_empty = use_default_for_empty
        self.languages = {language: "" for language in languages}
        self.set_content_for_languages(json_content)

    def set_content_for_languages(self, json_content):
        if not isinstance(json_content, str):
            get_request_logger().exception(
                f"Cannot set content to:\n{json_content}"
                f"\n{type(str)} expected, but received {type(json_content)}"
            )
            return
        if not json_content:
            return
        try:
            json_dict = json.loads(json_content)
        except JSONDecodeError as e:
            # If for some reason (i.e. old or corrupt data) the content given is not JSON,
            # use it as content for the default language.
            self.languages[settings.LANGUAGE_CODE] = json_content
            get_request_logger().exception(f"Unable to decode as JSON:\n{json_content}", exc_info=e)
            return

        for language, value in json_dict.items():
            self.languages[language] = value

    def __str__(self):
        """
        Return the content in the current language of the thread when called, to provide a seamless API to Django.
        Meaning that in most places, the object will appear as a localized string without any extra code.
        """
        return self[get_language()]

    def __repr__(self):
        return repr(self.languages)

    def __len__(self):
        return len(self.languages)

    def __getitem__(self, key):
        """
        Returns the string for the given language.
        """
        value = self.languages.get(key, "")
        if value or not self.use_default_for_empty:
            return value
        # If the value for the given language is empty and use_default_for_empty is set to True, provide the value of
        # the default language instead
        return self.languages[settings.LANGUAGE_CODE]

    def __setitem__(self, key, item: str):
        """
        Sets the content of the given language to the given string.
        """
        self.languages[key] = item

    def __eq__(self, other):
        if type(other) is not MultiLingualTextStructure:
            return False
        return (
                self.languages == other.languages
                and self.use_default_for_empty == other.use_default_for_empty
        )
