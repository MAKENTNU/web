from datetime import date
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django_hosts import reverse

from make_queue.models.course import Printer3DCourse
from users.models import User

COURSE_DATE = date(2026, 8, 25)


class TestPrinter3DCourseImportView(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_user("superuser", is_superuser=True)
        self.user = User.objects.create_user("user")

        self.url = reverse("printer_3d_course_import")

    @staticmethod
    def create_uploaded_file(contents: str, filename: str = "participants.csv"):
        return SimpleUploadedFile(filename, contents.encode(), content_type="text/csv")

    def post_file(self, contents: str, **extra_data):
        self.client.force_login(self.superuser)
        return self.client.post(
            self.url,
            {
                "file": self.create_uploaded_file(contents),
                "date": COURSE_DATE.isoformat(),
                "status": Printer3DCourse.Status.REGISTERED,
                "skip_already_registered": "on",
                **extra_data,
            },
        )

    def test_requires_permission_to_add_registrations(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, HTTPStatus.FORBIDDEN)

        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(self.url).status_code, HTTPStatus.OK)

    def test_posting_a_file_creates_the_registrations(self):
        response = self.post_file(
            "Name,Username\nOla Nordmann,olan\nKari Nordmann,karin\n"
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        result = response.context["import_result"]
        self.assertEqual(len(result.created), 2)
        self.assertTrue(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 2)
        self.assertEqual(Printer3DCourse.objects.get(username="olan").date, COURSE_DATE)

    def test_nothing_is_created_when_a_row_is_invalid(self):
        response = self.post_file(
            "Username,Card number\nolan,0123456789\nkarin,not a number\n"
        )

        result = response.context["import_result"]
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.failed), 1)
        self.assertFalse(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_the_valid_rows_are_created_when_asked_to_ignore_the_invalid_ones(self):
        response = self.post_file(
            "Username,Card number\nolan,0123456789\nkarin,not a number\n",
            import_valid_rows_only="on",
        )

        result = response.context["import_result"]
        self.assertTrue(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 1)

    def test_already_registered_participants_are_skipped(self):
        Printer3DCourse.objects.create(username="olan", date=COURSE_DATE)

        response = self.post_file("Username\nolan\nkarin\n")

        result = response.context["import_result"]
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(len(result.created), 1)

    def test_file_of_an_unsupported_format_is_rejected(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.url,
            {
                "file": SimpleUploadedFile("participants.pdf", b"Username\nolan"),
                "date": COURSE_DATE.isoformat(),
                "status": Printer3DCourse.Status.REGISTERED,
            },
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("import_result", response.context)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_file_without_a_username_column_is_rejected(self):
        response = self.post_file("Name,Card number\nOla Nordmann,0123456789\n")

        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Printer3DCourse.objects.count(), 0)
