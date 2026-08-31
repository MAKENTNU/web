from datetime import date
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django_hosts import reverse

from make_queue.models.course import Printer3DCourse
from users.models import User

COURSE_DATE = date(2026, 8, 25)
VALID_FILE = (
    "username,name,card_number,date\nolan,Ola Nordmann,,\nkarin,Kari Nordmann,,\n"
)
PARTLY_INVALID_FILE = (
    "username,name,card_number,date\nolan,,0123456789,\nkarin,,not a number,\n"
)


class TestPrinter3DCourseImportView(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_user("superuser", is_superuser=True)
        self.user = User.objects.create_user("user")

        self.url = reverse("printer_3d_course_import")

    def post_file(self, contents: str, **extra_data):
        self.client.force_login(self.superuser)
        return self.client.post(
            self.url,
            {
                "file": SimpleUploadedFile(
                    "participants.csv", contents.encode(), content_type="text/csv"
                ),
                "date": COURSE_DATE.isoformat(),
                "status": Printer3DCourse.Status.REGISTERED,
                "skip_already_registered": "on",
                **extra_data,
            },
        )

    def confirm(self):
        return self.client.post(self.url, {"confirm": "1"})

    def test_requires_permission_to_add_registrations(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, HTTPStatus.FORBIDDEN)

        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.url).status_code, HTTPStatus.OK)

    def test_uploading_a_file_only_previews_the_import(self):
        response = self.post_file(VALID_FILE)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["previewing"])
        self.assertTrue(response.context["will_import"])
        result = response.context["import_result"]
        self.assertEqual(len(result.created), 2)
        # Nothing should be written before the preview has been confirmed
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_confirming_the_preview_creates_the_registrations(self):
        self.post_file(VALID_FILE)
        response = self.confirm()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        result = response.context["import_result"]
        self.assertFalse(response.context["previewing"])
        self.assertTrue(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 2)
        self.assertEqual(Printer3DCourse.objects.get(username="olan").date, COURSE_DATE)

    def test_confirming_twice_does_not_import_twice(self):
        self.post_file(VALID_FILE)
        self.confirm()
        response = self.confirm()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Printer3DCourse.objects.count(), 2)

    def test_confirming_without_a_preview_is_rejected(self):
        self.client.force_login(self.superuser)
        response = self.confirm()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_starting_over_discards_the_preview(self):
        self.post_file(VALID_FILE)
        self.client.get(self.url)
        response = self.confirm()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_preview_shows_that_nothing_can_be_imported_when_a_row_is_invalid(self):
        response = self.post_file(PARTLY_INVALID_FILE)

        result = response.context["import_result"]
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.failed), 1)
        self.assertFalse(response.context["will_import"])

    def test_nothing_is_created_when_a_row_is_invalid(self):
        self.post_file(PARTLY_INVALID_FILE)
        self.confirm()

        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_the_valid_rows_are_created_when_asked_to_ignore_the_invalid_ones(self):
        response = self.post_file(PARTLY_INVALID_FILE, import_valid_rows_only="on")
        self.assertTrue(response.context["will_import"])

        self.confirm()
        self.assertEqual(Printer3DCourse.objects.count(), 1)

    def test_already_registered_participants_are_skipped(self):
        Printer3DCourse.objects.create(username="olan", date=COURSE_DATE)

        response = self.post_file(VALID_FILE)
        result = response.context["import_result"]
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(len(result.created), 1)

        self.confirm()
        self.assertEqual(Printer3DCourse.objects.count(), 2)

    def test_file_of_an_unsupported_format_is_rejected(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.url,
            {
                "file": SimpleUploadedFile("participants.pdf", b"username\nolan"),
                "date": COURSE_DATE.isoformat(),
                "status": Printer3DCourse.Status.REGISTERED,
            },
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("import_result", response.context)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_file_with_the_wrong_columns_is_rejected(self):
        response = self.post_file("name,card_number\nOla Nordmann,0123456789\n")

        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Printer3DCourse.objects.count(), 0)
