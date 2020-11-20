from unittest import TestCase

from . import test_test_utils_helper_funcs
from ..test_utils import mock_module_attrs


def original_func_monkey_patched(arg):
    return "patched", arg


class MockTests(TestCase):

    def test_mock_module_attrs_decorator(self):
        self.assert_original_func_returns_value("original")

        @mock_module_attrs({
            (test_test_utils_helper_funcs, 'original_func'): original_func_monkey_patched,
        })
        def assert_original_func_returns_monkey_patched_value(patched_value):
            self.assert_original_func_returns_value(patched_value)

        assert_original_func_returns_monkey_patched_value("patched")

        self.assert_original_func_returns_value("original")

    def assert_original_func_returns_value(self, return_value):
        self.assertTupleEqual(test_test_utils_helper_funcs.original_func(123), (return_value, 123))
