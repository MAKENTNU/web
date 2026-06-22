from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from users.models import User
from web.middleware import PageViewMiddleware
from web.models import PageView, Visitor


class PageViewMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session_middleware = SessionMiddleware(lambda r: HttpResponse())

    def _build_request(self, path="/some-page/", method="GET", user=None):
        request = getattr(self.factory, method.lower())(path)
        self.session_middleware.process_request(request)
        request.session.save()
        request.user = user or AnonymousUser()
        return request

    def _run(self, request, status=200):
        def get_response(_):
            r = HttpResponse()
            r.status_code = status
            return r

        return PageViewMiddleware(get_response)(request)

    def test_get_200_records_page_view(self):
        # A successful GET creates a `PageView` row with count 1.
        request = self._build_request(path="/test/")
        self._run(request)
        view = PageView.objects.get(path="/test/")
        self.assertEqual(view.count, 1)

    def test_repeat_visits_increment_count(self):
        # Repeated visits to the same path increment the existing row's count.
        for _ in range(3):
            request = self._build_request(path="/repeat/")
            self._run(request)
        self.assertEqual(PageView.objects.get(path="/repeat/").count, 3)

    def test_non_200_response_not_recorded(self):
        # 404s (and other non-200 responses) are not counted.
        request = self._build_request(path="/404/")
        self._run(request, status=404)
        self.assertFalse(PageView.objects.filter(path="/404/").exists())

    def test_post_request_not_recorded(self):
        # Non-GET methods (POST/PUT/...) are not counted.
        request = self._build_request(path="/form/", method="POST")
        self._run(request)
        self.assertFalse(PageView.objects.filter(path="/form/").exists())

    def test_static_path_ignored(self):
        # Paths matching `IGNORED_PREFIXES` (e.g. `/static/`) are skipped.
        request = self._build_request(path="/static/css/x.css")
        self._run(request)
        self.assertFalse(PageView.objects.filter(path="/static/css/x.css").exists())

    def test_anonymous_visitor_tracked_by_session(self):
        # Anonymous users get a `s:<session_key>` visitor identifier.
        request = self._build_request(path="/anon/")
        self._run(request)
        self.assertEqual(Visitor.objects.count(), 1)
        self.assertTrue(Visitor.objects.filter(identifier__startswith="s:").exists())

    def test_authenticated_visitor_tracked_by_user(self):
        # Logged-in users get a `u:<pk>` visitor identifier.
        user = User.objects.create_user("u1")
        request = self._build_request(path="/auth/", user=user)
        self._run(request)
        self.assertTrue(Visitor.objects.filter(identifier=f"u:{user.pk}").exists())

    def test_visitor_unique_across_visits(self):
        # Multiple visits from the same user create only one `Visitor` row.
        user = User.objects.create_user("u1")
        for path in ["/a/", "/b/", "/c/"]:
            request = self._build_request(path=path, user=user)
            self._run(request)
        self.assertEqual(Visitor.objects.filter(identifier=f"u:{user.pk}").count(), 1)

    def test_language_prefix_aggregated_to_canonical_path(self):
        # `/foo/`, `/en/foo/`, `/nb/foo/` all aggregate into `/foo/`.
        for path in ["/foo/", "/en/foo/", "/nb/foo/"]:
            request = self._build_request(path=path)
            self._run(request)
        self.assertFalse(PageView.objects.filter(path="/en/foo/").exists())
        self.assertFalse(PageView.objects.filter(path="/nb/foo/").exists())
        self.assertEqual(PageView.objects.get(path="/foo/").count, 3)

    def test_root_with_language_prefix_aggregated_to_root(self):
        # `/`, `/en/`, `/nb/` all aggregate into `/`.
        for path in ["/", "/en/", "/nb/"]:
            request = self._build_request(path=path)
            self._run(request)
        self.assertFalse(PageView.objects.filter(path="/en/").exists())
        self.assertFalse(PageView.objects.filter(path="/nb/").exists())
        self.assertEqual(PageView.objects.get(path="/").count, 3)
