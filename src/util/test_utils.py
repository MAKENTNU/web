import functools
import shutil
import tempfile
from abc import ABC
from collections.abc import Callable, Collection, Iterable
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any, Type, TypeVar
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, models, transaction
from django.db.models import QuerySet
from django.test import Client, SimpleTestCase, override_settings
from django.utils import translation
from django.utils.dateparse import parse_time

from users.models import User


T = TypeVar('T')
ModelT = TypeVar('ModelT', bound=models.Model)

# A very small JPEG image without any content; used for mocking a valid image while testing
MOCK_JPG_RAW = b'\xff\xd8\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04' \
               b'\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10' \
               b'\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11' \
               b'\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'

MOCK_JPG_FILE = SimpleUploadedFile(name="img.jpg", content=MOCK_JPG_RAW, content_type='image/jpeg')


# noinspection PyPep8Naming
class CleanUpTempFilesTestMixin(ABC):
    _temp_media_root: Path
    _override_settings_obj: override_settings

    @classmethod
    def setUpClass(cls):
        # noinspection PyUnresolvedReferences
        super().setUpClass()
        cls._temp_media_root = Path(tempfile.mkdtemp())
        cls._override_settings_obj = override_settings(MEDIA_ROOT=cls._temp_media_root)
        cls._override_settings_obj.enable()

    def tearDown(self):
        """
        Deletes all files and folders in the temp media root folder after each test case,
        as on some systems, they're not deleted before the next test case is run, which can cause filename collisions.

        It might be easier to just create the temp media root folder in ``setUp()`` (instead of ``setUpClass()``) and delete the whole folder
        in this method, but that would be slightly riskier, as it's not common to remember calling the super class' ``setUp()`` in a test case.
        """
        for child in self._temp_media_root.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()  # deletes the file/symlink
            elif child.is_dir():
                shutil.rmtree(child)

    @classmethod
    def tearDownClass(cls):
        cls._override_settings_obj.disable()
        shutil.rmtree(cls._temp_media_root)
        # noinspection PyUnresolvedReferences
        super().tearDownClass()


def mock_module_attrs(module_and_attrname_to_newattr: dict[tuple[Any, str], Any]):
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


# noinspection PyPep8Naming
def assertRaisesIntegrityError_withRollback(self: SimpleTestCase, transaction_func: Callable[[], None], *, raises: bool):
    if raises:
        with transaction.atomic(), self.assertRaises(IntegrityError):
            transaction_func()
    else:
        transaction_func()


# noinspection PyPep8Naming
def assertRedirectsWithPathPrefix(self: SimpleTestCase, response, expected_path_prefix: str):
    """
    Tests whether the provided ``response`` redirects, and whether the path of the redirect URL starts with the provided ``expected_path_prefix``.
    Also tests whether the redirect URL can be loaded by the same client that produced the provided ``response``.
    """
    self.assertEqual(response.status_code, HTTPStatus.FOUND)
    redirect_path = urlparse(response.url).path
    self.assertTrue(redirect_path.startswith(expected_path_prefix),
                    f"The redirected path {redirect_path} did not start with the expected prefix {expected_path_prefix}")

    def get_redirected_response(response_func: Callable):
        redirect_netloc = urlparse(response.url).netloc
        # If the redirect URL is on the same domain as the request that produced the response:
        if not redirect_netloc:
            return response_func()

        original_client_defaults: dict = response.client.defaults
        # Ensure that the client makes requests to the same netloc (domain) as the redirect URL
        response.client.defaults = {
            **original_client_defaults,
            'SERVER_NAME': redirect_netloc,
        }
        try:
            return response_func()
        finally:
            # Ensure that the `SERVER_NAME` we set earlier is reset
            response.client.defaults = original_client_defaults

    redirected_response = get_redirected_response(lambda: response.client.get(response.url))
    self.assertEqual(redirected_response.status_code, HTTPStatus.OK)


class PathPredicate(ABC):
    LANGUAGE_PREFIXES = ["", "/en"]

    def __init__(self, path: str, *, public: bool, translated=True):
        """
        :param path: the path to be tested (e.g. from ``reverse()``)
        :param public: whether a user does not have to be authenticated or not to successfully request the path
        :param translated: whether the path has a translated version (typically prefixed with e.g. ``/en``)
        """
        self.path = path
        self.public = public
        self.translated = translated

    def __repr__(self):
        return f"<{self.path} public={self.public} translated={self.translated}>"

    def do_request_assertion(self, client: Client, is_superuser: bool, test_case: SimpleTestCase):
        raise NotImplementedError

    @staticmethod
    def _prepend_url_path(prefix: str, url: str) -> str:
        url_obj = urlparse(url)
        if prefix:
            url_obj = url_obj._replace(path=f"{prefix}{url_obj.path}")
        return url_obj.geturl()


class Get(PathPredicate):

    def __init__(self, *args, redirect=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.redirect = redirect

    def do_request_assertion(self, client: Client, is_superuser: bool, test_case: SimpleTestCase):
        language_prefixes = self.LANGUAGE_PREFIXES if self.translated else [""]
        for prefix in language_prefixes:
            path = self._prepend_url_path(prefix, self.path)
            with test_case.subTest(path=path, is_superuser=is_superuser):
                self._do_request_assertion_for_path(path, prefix, client, is_superuser, test_case)

    def _do_request_assertion_for_path(self, path: str, language_prefix: str, client: Client, is_superuser: bool, test_case: SimpleTestCase):
        response = client.get(path)

        if self.redirect:
            test_case.assertIn(response.status_code, {HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.FOUND},
                               "The response did not redirect as expected.")
            # Follow the redirect URL from the response, and do the rest of the assertions from the perspective of this URL
            response = client.get(response.url)

        if self.public or is_superuser:
            test_case.assertEqual(response.status_code, HTTPStatus.OK)
        else:
            if response.status_code == HTTPStatus.FOUND:
                assertRedirectsWithPathPrefix(test_case, response, f"{language_prefix}/login/")
            else:
                test_case.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


def assert_requesting_paths_succeeds(self: SimpleTestCase, path_predicates: list[PathPredicate], subdomain=''):
    previous_language = translation.get_language()

    password = "1234"
    superuser = User.objects.create_user("unique_superuser_username", "admin@makentnu.no", password,
                                         is_superuser=True, is_staff=True)

    server_name = f'{subdomain}.{settings.PARENT_HOST}' if subdomain else settings.PARENT_HOST
    superuser_client = Client(SERVER_NAME=server_name)
    superuser_client.login(username=superuser.username, password=password)
    anon_client = Client(SERVER_NAME=server_name)

    for predicate in path_predicates:
        predicate.do_request_assertion(anon_client, False, self)
        predicate.do_request_assertion(superuser_client, True, self)

    # Reactivate the previously set language, as requests to translated URLs change the active language
    translation.activate(previous_language)


def generate_all_admin_urls_for_model_and_objs(model: Type[ModelT], model_objs: Iterable[ModelT]) -> list[str]:
    from web.tests.test_urls import reverse_admin  # Avoids circular importing

    url_name_prefix = f'{model._meta.app_label}_{model._meta.model_name}'
    return [
        reverse_admin(f'{url_name_prefix}_changelist'),
        reverse_admin(f'{url_name_prefix}_add'),
        *[
            reverse_admin(f'{url_name_prefix}_{url_name_suffix}', args=[obj.pk])
            for obj in model_objs
            for url_name_suffix in ['change', 'delete', 'history']
        ],
    ]


def set_without_duplicates(self: SimpleTestCase, collection: Collection[T] | QuerySet[T]) -> set[T]:
    collection_list = list(collection)
    collection_set = set(collection_list)
    self.assertEqual(len(collection_set), len(collection_list))
    return collection_set


def with_time(datetime_obj: datetime, time_str: str):
    time_obj = parse_time(time_str)
    return datetime_obj.replace(hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second)
