import json
from datetime import timedelta
from http import HTTPStatus

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from make_queue.models.machine import Machine, MachineType
from make_queue.models.reservation import Reservation
from users.models import User
from web.models import PageView, Visitor

INTERNAL_CLIENT_DEFAULTS = {"SERVER_NAME": f"i.{settings.PARENT_HOST}"}

# Avoids `ManifestStaticFilesStorage` lookups that fail without a built manifest.
STATIC_STORAGE_OVERRIDE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=STATIC_STORAGE_OVERRIDE)
class StatisticsViewTestBase(TestCase):
    def setUp(self):
        self.printer_type = MachineType.objects.get(pk=1)
        self.sewing_type = MachineType.objects.get(pk=2)
        self.printer = Machine.objects.create(
            name="Printer A", machine_type=self.printer_type
        )
        self.sewing = Machine.objects.create(
            name="Sewing A", machine_type=self.sewing_type
        )

        self.user = User.objects.create_user("internal_user")
        self.user.add_perms("internal.is_internal")

        self.anon_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.outsider_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        outsider = User.objects.create_user("outsider")
        self.outsider_client.force_login(outsider)
        self.client = Client(**INTERNAL_CLIENT_DEFAULTS)
        self.client.force_login(self.user)

        self.url = "/statistics/"
        self.data_url = "/api/statistics/data/"

    def make_reservation(self, machine, start, hours=1):
        # `bulk_create` skips `Reservation.save()` validation so we can plant
        # reservations at arbitrary timestamps (including in the past).
        Reservation.objects.bulk_create(
            [
                Reservation(
                    user=self.user,
                    machine=machine,
                    start_time=start,
                    end_time=start + timedelta(hours=hours),
                )
            ]
        )


class StatisticsPageAccessTests(StatisticsViewTestBase):
    def test_anonymous_user_redirected_or_denied(self):
        # Anonymous users cannot access the page.
        response = self.anon_client.get(self.url)
        self.assertIn(response.status_code, (HTTPStatus.FOUND, HTTPStatus.FORBIDDEN))

    def test_user_without_internal_perm_denied(self):
        # Logged-in users without `internal.is_internal` cannot access the page.
        response = self.outsider_client.get(self.url)
        self.assertIn(response.status_code, (HTTPStatus.FOUND, HTTPStatus.FORBIDDEN))

    def test_user_with_internal_perm_can_view(self):
        # Users with `internal.is_internal` get the page rendered with full context.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("machine_type_groups", response.context)
        self.assertIn("page_views", response.context)
        self.assertIn("time", response.context)

    def test_superuser_can_view(self):
        # Django superusers always pass `has_perm` checks.
        admin = User.objects.create_superuser("admin")
        admin_client = Client(**INTERNAL_CLIENT_DEFAULTS)
        admin_client.force_login(admin)
        response = admin_client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class StatisticsContextTests(StatisticsViewTestBase):
    def test_renders_each_machine_type_with_reservations(self):
        # Each machine type with at least one machine appears as its own section.
        now = timezone.now()
        self.make_reservation(self.printer, now - timedelta(days=2))
        response = self.client.get(self.url)
        groups = response.context["machine_type_groups"]
        slugs = [g["slug"] for g in groups]
        self.assertIn(f"mt-{self.printer_type.pk}", slugs)

    def test_special_reservations_excluded(self):
        # `special=True` reservations are filtered out so they don't inflate usage.
        now = timezone.now()
        Reservation.objects.bulk_create(
            [
                Reservation(
                    user=self.user,
                    machine=self.printer,
                    start_time=now,
                    end_time=now + timedelta(hours=1),
                    special=True,
                    special_text="x",
                )
            ]
        )
        response = self.client.get(self.url)
        printer_group = next(
            g
            for g in response.context["machine_type_groups"]
            if g["slug"] == f"mt-{self.printer_type.pk}"
        )
        self.assertEqual(printer_group["reservation_count"], 0)


class StatisticsFilterTests(StatisticsViewTestBase):
    def test_range_week_excludes_older_reservations(self):
        # `range_<slug>=week` keeps only reservations from the last 7 days.
        now = timezone.now()
        self.make_reservation(self.printer, now - timedelta(days=2))  # in range
        self.make_reservation(self.printer, now - timedelta(days=60))  # out of range
        slug = f"mt-{self.printer_type.pk}"

        response = self.client.get(self.url, {f"range_{slug}": "week"})
        group = next(
            g for g in response.context["machine_type_groups"] if g["slug"] == slug
        )
        self.assertEqual(group["reservation_count"], 1)

    def test_range_all_includes_everything(self):
        # No `range_<slug>` param defaults to "all time".
        now = timezone.now()
        self.make_reservation(self.printer, now - timedelta(days=2))
        self.make_reservation(self.printer, now - timedelta(days=60))
        slug = f"mt-{self.printer_type.pk}"

        response = self.client.get(self.url)
        group = next(
            g for g in response.context["machine_type_groups"] if g["slug"] == slug
        )
        self.assertEqual(group["reservation_count"], 2)

    def test_custom_range_with_from_and_to(self):
        # `range_<slug>=custom` with `from_`/`to_` params restricts to that interval.
        now = timezone.now()
        self.make_reservation(self.printer, now - timedelta(days=10))
        self.make_reservation(self.printer, now - timedelta(days=30))
        slug = f"mt-{self.printer_type.pk}"

        from_date = (now - timedelta(days=15)).date().isoformat()
        to_date = (now - timedelta(days=5)).date().isoformat()
        response = self.client.get(
            self.url,
            {
                f"range_{slug}": "custom",
                f"from_{slug}": from_date,
                f"to_{slug}": to_date,
            },
        )
        group = next(
            g for g in response.context["machine_type_groups"] if g["slug"] == slug
        )
        self.assertEqual(group["reservation_count"], 1)

    def test_filter_for_one_type_does_not_affect_another(self):
        # Filters are scoped per section — one section's filter shouldn't leak.
        now = timezone.now()
        self.make_reservation(self.printer, now - timedelta(days=60))
        self.make_reservation(self.sewing, now - timedelta(days=60))
        printer_slug = f"mt-{self.printer_type.pk}"
        sewing_slug = f"mt-{self.sewing_type.pk}"

        response = self.client.get(self.url, {f"range_{printer_slug}": "week"})
        groups = {g["slug"]: g for g in response.context["machine_type_groups"]}
        self.assertEqual(groups[printer_slug]["reservation_count"], 0)
        self.assertEqual(groups[sewing_slug]["reservation_count"], 1)


class StatisticsDataEndpointTests(StatisticsViewTestBase):
    def test_json_for_machine_type_key(self):
        # `key=mt-<pk>` returns the machine-type section's stats as JSON.
        now = timezone.now()
        self.make_reservation(self.printer, now - timedelta(days=1), hours=3)
        slug = f"mt-{self.printer_type.pk}"

        response = self.client.get(self.data_url, {"key": slug})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        body = json.loads(response.content)
        self.assertEqual(body["reservation_count"], 1)
        self.assertEqual(body["total_hours_sum"], 3.0)
        self.assertEqual(len(body["total_hours"]), 1)
        self.assertEqual(body["total_hours"][0]["name"], "Printer A")

    def test_json_for_time_key(self):
        # `key=time` returns the 24-bucket hourly distribution as JSON.
        response = self.client.get(self.data_url, {"key": "time"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        body = json.loads(response.content)
        self.assertIn("time", body)
        self.assertEqual(len(body["time"]), 24)

    def test_invalid_key_returns_400(self):
        # Unknown keys (not `time` or `mt-<pk>`) return 400.
        response = self.client.get(self.data_url, {"key": "junk"})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_invalid_mt_key_returns_400(self):
        # `mt-<non-numeric>` returns 400.
        response = self.client.get(self.data_url, {"key": "mt-abc"})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_unknown_mt_pk_returns_404(self):
        # `mt-<unknown pk>` returns 404.
        response = self.client.get(self.data_url, {"key": "mt-99999"})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_data_endpoint_respects_range_filter(self):
        # The endpoint applies `range_<slug>` URL params just like the page does.
        now = timezone.now()
        self.make_reservation(self.printer, now - timedelta(days=2))
        self.make_reservation(self.printer, now - timedelta(days=60))
        slug = f"mt-{self.printer_type.pk}"

        response = self.client.get(
            self.data_url,
            {
                "key": slug,
                f"range_{slug}": "week",
            },
        )
        body = json.loads(response.content)
        self.assertEqual(body["reservation_count"], 1)


class StatisticsPageViewsTests(StatisticsViewTestBase):
    def test_page_view_context_has_counts(self):
        # Site-traffic context aggregates `PageView` totals and `Visitor` count.
        PageView.objects.create(path="/x/", count=5)
        PageView.objects.create(path="/y/", count=3)
        Visitor.objects.create(identifier="u:1")
        Visitor.objects.create(identifier="u:2")

        response = self.client.get(self.url)
        page_views = response.context["page_views"]
        self.assertEqual(page_views["total_visits"], 8)
        self.assertEqual(page_views["unique_visitors"], 2)
        self.assertEqual(len(page_views["top_pages"]), 2)
        self.assertEqual(page_views["top_pages"][0]["path"], "/x/")
