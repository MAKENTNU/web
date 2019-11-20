import json
import logging
from json import JSONDecodeError

from django.utils.translation import get_language

from web import settings


class MultiLingualTextStructure:
    """
    Data structure to keep track of multilingual string data
    """
    supported_languages = list(map(lambda language: language[0], settings.LANGUAGES))

    def __init__(self, linear_content, use_default_for_empty):
        self.use_default_for_empty = use_default_for_empty
        self.languages = {language: "" for language in self.supported_languages}
        try:
            # Try to decode the data as JSON
            for language, value in json.loads(linear_content).items():
                self.languages[language] = value
        except JSONDecodeError as e:
            # If for some reason (i.e. old or corrupt data) the content given is not JSON,
            # use it as content for the default language.
            self.languages[settings.LANGUAGE_CODE] = linear_content
            logging.getLogger('django.request').exception(e)
        except TypeError as e:
            # If none or other incompatible type is passed
            logging.getLogger('django.request').exception(e)

    def __str__(self):
        """
        Return the content in the current language of the thread when called, to provide a seamless API to Django.
        Meaning that in most places, the object will appear as a localized string without any extra code.
        """
        return self[get_language()]

    def __repr__(self):
        return repr(self.languages)

    def __getitem__(self, key):
        """
        Returns the string for the given language
        """
        value = self.languages[key]
        if value or not self.use_default_for_empty:
            return value
        # If the value for the given language is empty and use_default_for_empty is set to True, provide the value of
        # the default language instead
        return self.languages[settings.LANGUAGE_CODE]

    def __setitem__(self, key, item: str):
        """
        Sets the content of the given language to the given string
        """
        self.languages[key] = item

    def __eq__(self, other):
        if type(other) is not MultiLingualTextStructure:
            return False
        if super().__eq__(other):
            return True
        return (
                self.languages == other.languages
                and self.use_default_for_empty == other.use_default_for_empty
        )
