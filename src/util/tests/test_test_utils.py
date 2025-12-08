from unittest import TestCase as StandardTestCase

from django.contrib.auth.models import Group
from django.test import TestCase

from users.models import User
from . import test_test_utils_helper_funcs
from ..test_utils import (
    generate_all_admin_urls_for_model_and_objs,
    mock_module_attrs,
    set_without_duplicates,
)


def original_func_monkey_patched(arg):
    return "patched", arg


class MockTests(StandardTestCase):
    def test_mock_module_attrs_decorator(self):
        self.assert_original_func_returns_value("original")

        @mock_module_attrs(
            {
                (
                    test_test_utils_helper_funcs,
                    "original_func",
                ): original_func_monkey_patched,
            }
        )
        def assert_original_func_returns_monkey_patched_value(patched_value):
            self.assert_original_func_returns_value(patched_value)

        assert_original_func_returns_monkey_patched_value("patched")

        self.assert_original_func_returns_value("original")

    def assert_original_func_returns_value(self, return_value):
        self.assertTupleEqual(
            test_test_utils_helper_funcs.original_func(123), (return_value, 123)
        )


class PathTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("user1")
        self.user2 = User.objects.create_user("user2")
        self.group1 = Group.objects.create(name="group1")

    def test__generate_all_admin_urls_for_model_and_objs__returns_as_expected(self):
        admin_url_scheme_and_host = "//admin.makentnu.localhost:8000"

        admin_urls = generate_all_admin_urls_for_model_and_objs(
            User, [self.user1, self.user2]
        )
        self.assertSetEqual(
            set_without_duplicates(self, admin_urls),
            {
                f"{admin_url_scheme_and_host}/users/user/",
                f"{admin_url_scheme_and_host}/users/user/add/",
                f"{admin_url_scheme_and_host}/users/user/1/change/",
                f"{admin_url_scheme_and_host}/users/user/1/delete/",
                f"{admin_url_scheme_and_host}/users/user/1/history/",
                f"{admin_url_scheme_and_host}/users/user/2/change/",
                f"{admin_url_scheme_and_host}/users/user/2/delete/",
                f"{admin_url_scheme_and_host}/users/user/2/history/",
            },
        )

        admin_urls = generate_all_admin_urls_for_model_and_objs(Group, [self.group1])
        self.assertSetEqual(
            set_without_duplicates(self, admin_urls),
            {
                f"{admin_url_scheme_and_host}/auth/group/",
                f"{admin_url_scheme_and_host}/auth/group/add/",
                f"{admin_url_scheme_and_host}/auth/group/1/change/",
                f"{admin_url_scheme_and_host}/auth/group/1/delete/",
                f"{admin_url_scheme_and_host}/auth/group/1/history/",
            },
        )
