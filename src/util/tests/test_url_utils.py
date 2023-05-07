from django.test import SimpleTestCase

from ..url_utils import urljoin_query


class UrlUtilsTests(SimpleTestCase):

    def test_urljoin_query_returns_expected_string(self):
        for base_path in ("/asdf/", "/asdf", "asdf/", "asdf"):
            with self.subTest(base_path=base_path):
                self.assertEqual(urljoin_query(f"{base_path}", {}), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}", ""), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}?", ""), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}", "?"), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}?", "?"), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}", "\n ?\n "), f"{base_path}")

                self.assertEqual(urljoin_query(f"{base_path}?a=1", {"b": 2}), f"{base_path}?a=1&b=2")
                self.assertEqual(urljoin_query(f"{base_path}?a=1", "b=2"), f"{base_path}?a=1&b=2")
                self.assertEqual(urljoin_query(f"{base_path}?a=1", "?b=2"), f"{base_path}?a=1&b=2")
                self.assertEqual(urljoin_query(f"{base_path}?a=1", "\n ?b=2\n "), f"{base_path}?a=1&b=2")

                # Params with the same name are overwritten instead of added;
                # this should maybe be fixed in the future, but isn't a big problem as of now
                self.assertEqual(urljoin_query(f"{base_path}?a=1", {"a": 2}), f"{base_path}?a=2")
                self.assertEqual(urljoin_query(f"{base_path}?a=1", "a=2"), f"{base_path}?a=2")

                self.assertEqual(urljoin_query(f"{base_path}?a=2&a=1", {}), f"{base_path}?a=1")
                self.assertEqual(urljoin_query(f"{base_path}?a=1&a=2", ""), f"{base_path}?a=2")
                self.assertEqual(urljoin_query(f"{base_path}?a=2&a=1", {"a": 3}), f"{base_path}?a=3")
                self.assertEqual(urljoin_query(f"{base_path}?a=1&a=2", "a=3"), f"{base_path}?a=3")

                self.assertEqual(urljoin_query(f"{base_path}", {"a": 2, "b": 2, "c": 2}), f"{base_path}?a=2&b=2&c=2")
                self.assertEqual(urljoin_query(f"{base_path}", "a=2&b=2&c=2"), f"{base_path}?a=2&b=2&c=2")

                self.assertEqual(urljoin_query(f"{base_path}?a=1&b=1", {"a": 3, "b": 3, "c": 3}), f"{base_path}?a=3&b=3&c=3")
                self.assertEqual(urljoin_query(f"{base_path}?a=1&b=1", "a=3&b=3&c=3"), f"{base_path}?a=3&b=3&c=3")
