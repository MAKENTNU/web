import functools
from abc import ABC
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.utils import translation

from users.models import User

# A very small JPEG image without any content; used for mocking a valid image while testing
MOCK_JPG_RAW = b'\xff\xd8\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04' \
               b'\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10' \
               b'\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11' \
               b'\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'

MOCK_JPG_FILE = SimpleUploadedFile(name="img.jpg", content=MOCK_JPG_RAW, content_type='image/jpeg')


def mock_module_attrs(module_and_attrname_to_newattr: Dict[Tuple[Any, str], Any]):
    """
    A decorator for monkey patching attributes of modules while the decorated function is executed;
    the original module attributes are monkey patched back after execution.

    This can be useful when testing code that e.g. calls functions that are hard to mock;
    these functions can instead be replaced by mock functions.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            module_and_attrname_to_oldattr = {}
            for module_and_attrname, new_attr in module_and_attrname_to_newattr.items():
                module, attr_name = module_and_attrname
                module_and_attrname_to_oldattr[module_and_attrname] = getattr(module, attr_name)
                setattr(module, attr_name, new_attr)

            value = func(*args, **kwargs)

            for module_and_attrname, old_attr in module_and_attrname_to_oldattr.items():
                module, attr_name = module_and_attrname
                setattr(module, attr_name, old_attr)

            return value

        return wrapper

    return decorator


class PathPredicate(ABC):
    LANGUAGE_PREFIXES = ["", "/en"]

    def __init__(self, path: str, *, public: bool, translated=True, success_code=200):
        """
        :param path: the path to be tested (e.g. from ``reverse()``)
        :param public: whether a user does not have to be authenticated or not to successfully request the path
        :param translated: whether the path has a translated version (typically prefixed with e.g. ``/en``)
        :param success_code: the HTTP status code of a response that indicates that the request was successful.
                             If the code provided is a redirect code (3xx), the redirect chain will be followed until a status of 200 is encountered.
        """
        if translated:
            self.paths = []
            for prefix in self.LANGUAGE_PREFIXES:
                url_obj = urlparse(path)
                url_obj = url_obj._replace(path=f"{prefix}{url_obj.path}")
                self.paths.append(url_obj.geturl())
        else:
            self.paths = [path]

        self.public = public
        self.translated = translated
        self.success_code = success_code

    def __repr__(self):
        return "\n".join(self.paths)

    def do_request_assertion(self, path: str, client: Client, is_superuser: bool, test_case: SimpleTestCase):
        raise NotImplementedError


class Get(PathPredicate):

    def do_request_assertion(self, path: str, client: Client, is_superuser: bool, test_case: SimpleTestCase):
        status_code = client.get(path).status_code

        if 300 <= self.success_code < 400:
            test_case.assertEqual(status_code, self.success_code)
            status_code = client.get(path, follow=True).status_code

        if self.public or is_superuser:
            test_case.assertEqual(status_code, 200)
        else:
            test_case.assertGreaterEqual(status_code, 300)


def assert_requesting_paths_succeeds(self: SimpleTestCase, path_predicates: List[PathPredicate], subdomain=''):
    previous_language = translation.get_language()

    password = "1234"
    superuser = User.objects.create_user("superuser", "admin@makentnu.no", password,
                                         is_superuser=True, is_staff=True)

    server_name = f'{subdomain}.testserver' if subdomain else 'testserver'  # 'testserver' is Django's default server name
    superuser_client = Client(SERVER_NAME=server_name)
    superuser_client.login(username=superuser.username, password=password)
    anon_client = Client(SERVER_NAME=server_name)

    for predicate in path_predicates:
        for path in predicate.paths:
            with self.subTest(path=path):
                predicate.do_request_assertion(path, anon_client, False, self)
                predicate.do_request_assertion(path, superuser_client, True, self)

    # Reactivate the previously set language, as requests to translated URLs change the active language
    translation.activate(previous_language)


class PermissionsTestCase(TestCase):

    @staticmethod
    def add_permissions(user: User, *codenames: str):
        user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
