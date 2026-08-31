import io
from datetime import date
from unittest.mock import patch

import xlsxwriter
from django.core.files.base import ContentFile
from django.test import TestCase

from util.spreadsheet_utils import (
    SpreadsheetReadError,
    excel_serial_to_date,
    read_rows,
)


def create_csv_file(contents: bytes, filename: str = "participants.csv") -> ContentFile:
    return ContentFile(contents, name=filename)


def create_xlsx_file(rows: list[list], filename: str = "participants.xlsx"):
    output_file = io.BytesIO()
    workbook = xlsxwriter.Workbook(output_file, {"in_memory": True})
    worksheet = workbook.add_worksheet("Participants")
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            worksheet.write(row_index, column_index, value)
    workbook.close()
    return ContentFile(output_file.getvalue(), name=filename)


class TestReadRows(TestCase):
    def test_reads_comma_separated_file(self):
        file = create_csv_file(b"Name,Username\nOla Nordmann,olan\n")
        self.assertEqual(
            read_rows(file), [["Name", "Username"], ["Ola Nordmann", "olan"]]
        )

    def test_reads_semicolon_separated_file(self):
        file = create_csv_file(b"Name;Username\nOla Nordmann;olan\n")
        self.assertEqual(
            read_rows(file), [["Name", "Username"], ["Ola Nordmann", "olan"]]
        )

    def test_reads_file_with_a_single_column(self):
        file = create_csv_file(b"olan\nkarin\n")
        self.assertEqual(read_rows(file), [["olan"], ["karin"]])

    def test_reads_file_with_byte_order_mark_and_non_ascii_letters(self):
        file = create_csv_file("Navn\nBjørn Åsmundsen\n".encode("utf-8-sig"))
        self.assertEqual(read_rows(file), [["Navn"], ["Bjørn Åsmundsen"]])

    def test_reads_file_encoded_as_windows_1252(self):
        file = create_csv_file("Navn\nBjørn Åsmundsen\n".encode("cp1252"))
        self.assertEqual(read_rows(file), [["Navn"], ["Bjørn Åsmundsen"]])

    def test_strips_cells_and_removes_trailing_empty_rows_and_columns(self):
        file = create_csv_file(b"Name,Username,,\n  Ola Nordmann , olan ,,\n,,,\n")
        self.assertEqual(
            read_rows(file), [["Name", "Username"], ["Ola Nordmann", "olan"]]
        )

    def test_pads_rows_to_the_same_length(self):
        file = create_csv_file(b"Name,Username\nOla Nordmann\n")
        self.assertEqual(read_rows(file), [["Name", "Username"], ["Ola Nordmann", ""]])

    def test_reads_xlsx_file(self):
        file = create_xlsx_file(
            [
                ["Name", "Username", "Card number"],
                ["Ola Nordmann", "olan", "0123456789"],
                ["Kari Nordmann", "karin", ""],
            ]
        )
        self.assertEqual(
            read_rows(file),
            [
                ["Name", "Username", "Card number"],
                ["Ola Nordmann", "olan", "0123456789"],
                ["Kari Nordmann", "karin", ""],
            ],
        )

    def test_reads_numbers_of_xlsx_file_without_a_trailing_decimal_point(self):
        file = create_xlsx_file([["Username", "Card number"], ["olan", 123456789]])
        self.assertEqual(
            read_rows(file), [["Username", "Card number"], ["olan", "123456789"]]
        )

    def test_reads_xlsx_file_with_holes_in_it(self):
        # Cells that have never been written to are left out of the file entirely
        output_file = io.BytesIO()
        workbook = xlsxwriter.Workbook(output_file, {"in_memory": True})
        worksheet = workbook.add_worksheet()
        worksheet.write("A1", "Name")
        worksheet.write("C1", "Username")
        worksheet.write("C2", "olan")
        workbook.close()
        file = ContentFile(output_file.getvalue(), name="participants.xlsx")

        self.assertEqual(read_rows(file), [["Name", "", "Username"], ["", "", "olan"]])

    def test_unsupported_file_format_is_rejected(self):
        file = ContentFile(b"Name,Username", name="participants.pdf")
        with self.assertRaises(SpreadsheetReadError):
            read_rows(file)

    def test_corrupt_xlsx_file_is_rejected(self):
        file = ContentFile(b"Definitely not a ZIP archive", name="participants.xlsx")
        with self.assertRaises(SpreadsheetReadError):
            read_rows(file)

    def test_xlsx_file_that_decompresses_to_a_huge_file_is_rejected(self):
        file = create_xlsx_file([["Username"], ["olan"]])
        with (
            patch("util.spreadsheet_utils.MAX_UNCOMPRESSED_XLSX_SIZE", 10),
            self.assertRaises(SpreadsheetReadError),
        ):
            read_rows(file)

    def test_empty_file_is_read_as_no_rows(self):
        self.assertEqual(read_rows(create_csv_file(b"")), [])


class TestExcelSerialToDate(TestCase):
    def test_serial_numbers_within_the_date_range_are_converted(self):
        self.assertEqual(excel_serial_to_date("45000"), date(2023, 3, 15))
        self.assertEqual(excel_serial_to_date("45000.5"), date(2023, 3, 15))

    def test_values_that_are_not_dates_are_not_converted(self):
        for value in ("", "olan", "42", "0123456789", "9999999999"):
            with self.subTest(value=value):
                self.assertIsNone(excel_serial_to_date(value))
