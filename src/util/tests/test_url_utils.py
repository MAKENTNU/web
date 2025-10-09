from django.conf import settings
from django.test import SimpleTestCase

from ..url_utils import get_reverse_host_kwargs_from_url, urljoin_query


class UrlUtilsTests(SimpleTestCase):
    def test_urljoin_query_returns_expected_string(self):
        for base_path in ("/asdf/", "/asdf", "asdf/", "asdf"):
            with self.subTest(base_path=base_path):
                self.assertEqual(urljoin_query(f"{base_path}", {}), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}", ""), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}?", ""), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}", "?"), f"{base_path}")
                self.assertEqual(urljoin_query(f"{base_path}?", "?"), f"{base_path}")
                self.assertEqual(
                    urljoin_query(f"{base_path}", "\n ?\n "), f"{base_path}"
                )

                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1", {"b": 2}), f"{base_path}?a=1&b=2"
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1", "b=2"), f"{base_path}?a=1&b=2"
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1", "?b=2"), f"{base_path}?a=1&b=2"
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1", "\n ?b=2\n "),
                    f"{base_path}?a=1&b=2",
                )

                # Params with the same name are overwritten instead of added;
                # this should maybe be fixed in the future, but isn't a big problem as of now
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1", {"a": 2}), f"{base_path}?a=2"
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1", "a=2"), f"{base_path}?a=2"
                )

                self.assertEqual(
                    urljoin_query(f"{base_path}?a=2&a=1", {}), f"{base_path}?a=1"
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1&a=2", ""), f"{base_path}?a=2"
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=2&a=1", {"a": 3}), f"{base_path}?a=3"
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1&a=2", "a=3"), f"{base_path}?a=3"
                )

                self.assertEqual(
                    urljoin_query(f"{base_path}", {"a": 2, "b": 2, "c": 2}),
                    f"{base_path}?a=2&b=2&c=2",
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}", "a=2&b=2&c=2"),
                    f"{base_path}?a=2&b=2&c=2",
                )

                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1&b=1", {"a": 3, "b": 3, "c": 3}),
                    f"{base_path}?a=3&b=3&c=3",
                )
                self.assertEqual(
                    urljoin_query(f"{base_path}?a=1&b=1", "a=3&b=3&c=3"),
                    f"{base_path}?a=3&b=3&c=3",
                )

    def test_get_reverse_host_kwargs_from_url_returns_expected_host_object(self):
        def assert_url_returns(
            *, url_subdomain: str, expected_host: str, expected_host_args: str | None
        ):
            host_kwargs = get_reverse_host_kwargs_from_url(
                f"{scheme}{url_subdomain}{settings.PARENT_HOST}{path}"
            )
            self.assertDictEqual(
                host_kwargs, {"host": expected_host, "host_args": expected_host_args}
            )

        def get_expected_value_error_message(url_: str):
            return f"The passed URL ({url_}) must be internal, i.e. makentnu.localhost:8000 must be part of the URL's host."

        for scheme in ("http://", "https://", "//"):
            for path in ("", "/", "/asdf/", "/asdf/?qwer=2"):
                with self.subTest(scheme=scheme, path=path):
                    assert_url_returns(
                        url_subdomain="", expected_host="main", expected_host_args=None
                    )
                    assert_url_returns(
                        url_subdomain=".", expected_host="main", expected_host_args=None
                    )
                    assert_url_returns(
                        url_subdomain="i.",
                        expected_host="internal",
                        expected_host_args="i",
                    )
                    assert_url_returns(
                        url_subdomain="internal.",
                        expected_host="internal",
                        expected_host_args="internal",
                    )
                    assert_url_returns(
                        url_subdomain="internt.",
                        expected_host="internal",
                        expected_host_args="internt",
                    )
                    assert_url_returns(
                        url_subdomain="admin.",
                        expected_host="admin",
                        expected_host_args=None,
                    )
                    assert_url_returns(
                        url_subdomain="docs.",
                        expected_host="docs",
                        expected_host_args=None,
                    )

                    url = f"{scheme}makentnu.no{path}"
                    with self.assertRaisesMessage(
                        ValueError, get_expected_value_error_message(url)
                    ):
                        get_reverse_host_kwargs_from_url(url)

                    url = f"{scheme}i.makentnu.localhost{path}"
                    with self.assertRaisesMessage(
                        ValueError, get_expected_value_error_message(url)
                    ):
                        get_reverse_host_kwargs_from_url(url)
