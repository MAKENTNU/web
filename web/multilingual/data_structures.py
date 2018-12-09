import json
from django.utils.translation import get_language
from json import JSONDecodeError

from web import settings


class MultiLingualTextStructure:
    supported_languages = list(map(lambda language: language[0], settings.LANGUAGES))

    def __init__(self, linear_content, use_default_for_empty):
        self.use_default_for_empty = use_default_for_empty
        self.languages = {language: "" for language in self.supported_languages}
        try:
            for language, value in json.loads(linear_content).items():
                self.languages[language] = value
        except JSONDecodeError:
            self.languages[settings.LANGUAGE_CODE] = linear_content

    def __str__(self):
        return self[get_language()]

    def __getitem__(self, key):
        value = self.languages[key]
        if value or not self.use_default_for_empty:
            return value
        return self.languages[settings.LANGUAGE_CODE]

    def __setitem__(self, key, item):
        self.languages[key] = item