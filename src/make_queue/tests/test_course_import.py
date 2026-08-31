from datetime import date

from django.test import TestCase

from make_queue.course_import import (
    COLUMNS,
    MAX_NUM_ROWS,
    CourseImportError,
    ImportedRow,
    import_registrations,
    parse_date,
    parse_rows,
)
from make_queue.models.course import CoursePermission, Printer3DCourse

DEFAULT_DATE = date(2026, 8, 25)


class TestParseRows(TestCase):
    def test_reads_a_file_with_the_expected_columns(self):
        rows = parse_rows(
            [
                ["username", "name", "card_number", "date"],
                ["olan", "Ola Nordmann", "0123456789", "2026-08-25"],
            ]
        )
        self.assertEqual(
            rows,
            [
                ImportedRow(
                    line_number=2,
                    name="Ola Nordmann",
                    username="olan",
                    card_number="0123456789",
                    date_string="2026-08-25",
                )
            ],
        )

    def test_the_header_row_is_matched_regardless_of_case_and_padding(self):
        rows = parse_rows(
            [[" Username", "NAME ", "Card_Number", "Date"], ["olan", "", "", ""]]
        )
        self.assertEqual(rows, [ImportedRow(line_number=2, username="olan")])

    def test_only_the_username_has_to_be_filled_in(self):
        rows = parse_rows([list(COLUMNS), ["olan", "", "", ""]])
        self.assertEqual(rows, [ImportedRow(line_number=2, username="olan")])

    def test_skips_empty_rows(self):
        rows = parse_rows(
            [
                list(COLUMNS),
                ["olan", "", "", ""],
                ["", "", "", ""],
                ["karin", "", "", ""],
            ]
        )
        self.assertEqual([row.username for row in rows], ["olan", "karin"])
        # The line numbers should still match the ones of the file
        self.assertEqual([row.line_number for row in rows], [2, 4])

    def test_file_with_the_columns_in_another_order_is_rejected(self):
        with self.assertRaises(CourseImportError):
            parse_rows(
                [["name", "username", "card_number", "date"], ["Ola", "olan", "", ""]]
            )

    def test_file_with_differently_named_columns_is_rejected(self):
        with self.assertRaises(CourseImportError):
            parse_rows(
                [["brukernavn", "navn", "kortnummer", "dato"], ["olan", "", "", ""]]
            )

    def test_file_with_missing_columns_is_rejected(self):
        with self.assertRaises(CourseImportError):
            parse_rows([["username"], ["olan"]])

    def test_file_without_a_header_row_is_rejected(self):
        with self.assertRaises(CourseImportError):
            parse_rows([["olan", "Ola Nordmann", "", ""]])

    def test_empty_file_is_rejected(self):
        with self.assertRaises(CourseImportError):
            parse_rows([])

    def test_file_with_only_a_header_row_is_rejected(self):
        with self.assertRaises(CourseImportError):
            parse_rows([list(COLUMNS)])

    def test_too_long_file_is_rejected(self):
        rows = [
            list(COLUMNS),
            *[[f"user{i}", "", "", ""] for i in range(MAX_NUM_ROWS + 1)],
        ]
        with self.assertRaises(CourseImportError):
            parse_rows(rows)


class TestParseDate(TestCase):
    def test_parses_iso_formatted_dates(self):
        self.assertEqual(parse_date("2026-08-25"), date(2026, 8, 25))
        self.assertEqual(parse_date(" 2026-08-25 "), date(2026, 8, 25))

    def test_parses_excel_serial_numbers(self):
        self.assertEqual(parse_date("46259"), date(2026, 8, 25))

    def test_returns_none_for_values_in_any_other_format(self):
        for date_string in (
            "",
            "  ",
            "the 25th",
            "2026-13-25",
            "25.08.2026",
            "25/08/2026",
        ):
            with self.subTest(date_string=date_string):
                self.assertIsNone(parse_date(date_string))


class TestImportRegistrations(TestCase):
    def setUp(self):
        self.course_permissions = list(
            CoursePermission.objects.filter(short_name="R3DP")
        )

    def import_(self, rows: list[ImportedRow], **kwargs):
        return import_registrations(
            rows,
            default_date=DEFAULT_DATE,
            status=Printer3DCourse.Status.REGISTERED,
            course_permissions=self.course_permissions,
            **kwargs,
        )

    def test_creates_a_registration_per_row(self):
        result = self.import_(
            [
                ImportedRow(line_number=1, name="Ola Nordmann", username="olan"),
                ImportedRow(line_number=2, name="Kari Nordmann", username="karin"),
            ]
        )

        self.assertEqual(len(result.created), 2)
        self.assertTrue(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 2)
        registration = Printer3DCourse.objects.get(username="olan")
        self.assertEqual(registration.name, "Ola Nordmann")
        self.assertEqual(registration.date, DEFAULT_DATE)
        self.assertEqual(registration.status, Printer3DCourse.Status.REGISTERED)
        # The base permission should always be added, in addition to the selected ones
        self.assertSetEqual(set(registration.permission_names), {"3DPR", "R3DP"})

    def test_uses_the_date_of_the_row_when_it_has_one(self):
        self.import_(
            [ImportedRow(line_number=1, username="olan", date_string="2003-02-01")]
        )
        self.assertEqual(
            Printer3DCourse.objects.get(username="olan").date, date(2003, 2, 1)
        )

    def test_usernames_are_lowercased(self):
        self.import_([ImportedRow(line_number=1, username="OlaN")])
        self.assertTrue(Printer3DCourse.objects.filter(username="olan").exists())

    def test_already_registered_usernames_are_skipped(self):
        Printer3DCourse.objects.create(username="olan", date=DEFAULT_DATE)

        result = self.import_(
            [
                ImportedRow(line_number=1, username="olan"),
                ImportedRow(line_number=2, username="karin"),
            ]
        )

        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(len(result.created), 1)
        self.assertTrue(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 2)

    def test_already_registered_usernames_are_errors_when_not_skipping(self):
        Printer3DCourse.objects.create(username="olan", date=DEFAULT_DATE)

        result = self.import_(
            [ImportedRow(line_number=1, username="olan")],
            skip_already_registered=False,
        )

        self.assertEqual(len(result.failed), 1)
        self.assertFalse(result.committed)

    def test_rows_without_a_username_are_errors(self):
        result = self.import_([ImportedRow(line_number=1, name="Ola Nordmann")])
        self.assertEqual(len(result.failed), 1)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_duplicate_usernames_within_the_file_are_errors(self):
        result = self.import_(
            [
                ImportedRow(line_number=1, username="olan"),
                ImportedRow(line_number=2, username="OLAN"),
            ]
        )
        self.assertEqual(len(result.failed), 1)
        self.assertEqual(len(result.created), 1)

    def test_unparsable_dates_are_errors(self):
        result = self.import_(
            [ImportedRow(line_number=1, username="olan", date_string="25.08.2026")]
        )
        self.assertEqual(len(result.failed), 1)

    def test_invalid_card_numbers_are_errors(self):
        result = self.import_(
            [ImportedRow(line_number=1, username="olan", card_number="not a number")]
        )
        self.assertEqual(len(result.failed), 1)
        self.assertFalse(result.committed)

    def test_nothing_is_created_when_any_row_is_invalid(self):
        result = self.import_(
            [
                ImportedRow(line_number=1, username="olan"),
                ImportedRow(line_number=2, username=""),
            ]
        )

        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.failed), 1)
        self.assertFalse(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_a_dry_run_reports_the_outcome_without_writing_anything(self):
        Printer3DCourse.objects.create(username="karin", date=DEFAULT_DATE)

        result = self.import_(
            [
                ImportedRow(line_number=1, username="olan"),
                ImportedRow(line_number=2, username="karin"),
                ImportedRow(line_number=3, username=""),
            ],
            dry_run=True,
        )

        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(len(result.failed), 1)
        self.assertFalse(result.committed)
        # Only the registration that existed before the dry run should remain
        self.assertEqual(Printer3DCourse.objects.count(), 1)

    def test_a_dry_run_of_a_valid_file_writes_nothing(self):
        result = self.import_(
            [ImportedRow(line_number=1, username="olan")], dry_run=True
        )

        self.assertEqual(len(result.created), 1)
        self.assertFalse(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 0)

    def test_valid_rows_are_created_when_asked_to_ignore_the_invalid_ones(self):
        result = self.import_(
            [
                ImportedRow(line_number=1, username="olan"),
                ImportedRow(line_number=2, username=""),
            ],
            import_valid_rows_only=True,
        )

        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.failed), 1)
        self.assertTrue(result.committed)
        self.assertEqual(Printer3DCourse.objects.count(), 1)
