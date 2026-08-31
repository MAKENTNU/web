"""
Reading of simple tabular files - currently CSV and XLSX - as rows of strings.

Only the parts of the XLSX format that are needed for reading a plain sheet of values
are implemented, which avoids adding a dependency on a full-fledged spreadsheet
library; styling is ignored, and formulas are read as their last cached value.
"""

import csv
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from pathlib import PurePosixPath

from django.core.files import File
from django.utils.translation import gettext_lazy as _

CSV_SUFFIXES = (".csv", ".tsv", ".txt")
XLSX_SUFFIXES = (".xlsx",)
SUPPORTED_SUFFIXES = CSV_SUFFIXES + XLSX_SUFFIXES

# Excel counts dates as the number of days since 1900-01-01, but also counts the
# non-existent 1900-02-29, which makes 1899-12-30 the epoch that its serial numbers
# should be added to
EXCEL_DATE_EPOCH = date(1899, 12, 30)
# Serial numbers outside this range are far more likely to be something else than a
# date - like a card number
MIN_EXCEL_DATE_SERIAL = 10_000  # 1927-05-18
MAX_EXCEL_DATE_SERIAL = 80_000  # 2119-01-24

_SPREADSHEET_ML_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_PACKAGE_RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_DOC_RELS_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

_WORKBOOK_PATH = "xl/workbook.xml"
_WORKBOOK_RELS_PATH = "xl/_rels/workbook.xml.rels"
_SHARED_STRINGS_PATH = "xl/sharedStrings.xml"
_FALLBACK_WORKSHEET_PATH = "xl/worksheets/sheet1.xml"

# A small XLSX file can decompress to an arbitrarily large one, so its uncompressed
# size must be checked before any of it is read into memory
MAX_UNCOMPRESSED_XLSX_SIZE = 100 * 1024 * 1024  # 100 MiB

_CELL_REFERENCE_REGEX = re.compile(r"^([A-Z]+)\d+$")
_INTEGRAL_FLOAT_REGEX = re.compile(r"^(-?\d+)\.0+$")

# The number of bytes of a CSV file that are inspected to detect its delimiter
_CSV_SNIFF_SIZE = 4096
_CSV_DELIMITERS = ",;\t"


class SpreadsheetReadError(Exception):
    """Raised when a file cannot be read as a spreadsheet."""


def read_rows(file: File, filename: str = None) -> list[list[str]]:
    """
    Read the given CSV or XLSX file as a list of rows of stripped strings.

    Rows are padded to the length of the longest row, and both trailing empty cells and
    trailing empty rows are removed. For XLSX files, only the first sheet is read.

    :param file: The file to read; must be opened in binary mode
    :param filename: The name to detect the file format from; defaults to ``file.name``
    :return: The rows of the file
    :raises SpreadsheetReadError: If the file is of an unsupported format, or is corrupt
    """
    filename = filename if filename is not None else (file.name or "")
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(SUPPORTED_SUFFIXES)
        raise SpreadsheetReadError(
            _("Unsupported file format “%(suffix)s”. Supported formats: %(supported)s")
            % {"suffix": suffix or filename, "supported": supported}
        )

    file.seek(0)
    contents = file.read()
    rows = _read_xlsx(contents) if suffix in XLSX_SUFFIXES else _read_csv(contents)
    return _normalize_rows(rows)


def excel_serial_to_date(value: str) -> date | None:
    """
    Convert an Excel date serial number to a date, or return ``None`` if the value is
    not a number within the range of serial numbers that are treated as dates.
    """
    try:
        serial = float(value)
    except ValueError:
        return None
    if not MIN_EXCEL_DATE_SERIAL <= serial <= MAX_EXCEL_DATE_SERIAL:
        return None
    return EXCEL_DATE_EPOCH + timedelta(days=int(serial))


def _normalize_rows(rows: list[list[str]]) -> list[list[str]]:
    rows = [[cell.strip() for cell in row] for row in rows]
    while rows and not any(rows[-1]):
        rows.pop()
    if not rows:
        return []

    num_columns = max(len(row) for row in rows)
    # Remove columns that are empty in every row, but only trailing ones, as removing
    # them from the middle would shift the remaining columns out of place
    while num_columns and not any(
        len(row) >= num_columns and row[num_columns - 1] for row in rows
    ):
        num_columns -= 1

    return [(row + [""] * num_columns)[:num_columns] for row in rows]


def _read_csv(contents: bytes) -> list[list[str]]:
    text = _decode(contents)
    try:
        dialect = csv.Sniffer().sniff(
            text[:_CSV_SNIFF_SIZE], delimiters=_CSV_DELIMITERS
        )
    except csv.Error:
        # A file with just a single column has no delimiter to detect
        dialect = csv.excel
    return list(csv.reader(io.StringIO(text, newline=""), dialect))


def _decode(contents: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise SpreadsheetReadError(
        _("The file is neither valid UTF-8 nor valid Windows-1252 encoded text.")
    )


def _read_xlsx(contents: bytes) -> list[list[str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as archive:
            _check_uncompressed_size(archive)
            shared_strings = _read_shared_strings(archive)
            worksheet_path = _find_first_worksheet_path(archive)
            with archive.open(worksheet_path) as worksheet_file:
                worksheet = ET.parse(worksheet_file).getroot()
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
        raise SpreadsheetReadError(
            _("The file could not be read as an XLSX file; is it corrupt?")
        ) from e

    rows = []
    for row_element in worksheet.iter(f"{_SPREADSHEET_ML_NS}row"):
        row: list[str] = []
        for cell_element in row_element.iterfind(f"{_SPREADSHEET_ML_NS}c"):
            column_index = _column_index(cell_element.get("r"), default=len(row))
            # Cells that are empty are simply left out of the file
            row.extend([""] * (column_index - len(row)))
            row.append(_cell_value(cell_element, shared_strings))
        rows.append(row)
    return rows


def _check_uncompressed_size(archive: zipfile.ZipFile) -> None:
    uncompressed_size = sum(info.file_size for info in archive.infolist())
    if uncompressed_size > MAX_UNCOMPRESSED_XLSX_SIZE:
        raise SpreadsheetReadError(
            _("The contents of the file are too big to be read.")
        )


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if _SHARED_STRINGS_PATH not in archive.namelist():
        return []
    with archive.open(_SHARED_STRINGS_PATH) as shared_strings_file:
        root = ET.parse(shared_strings_file).getroot()
    # A string can be split into several runs (`r`) of differently formatted text, so
    # all the text elements (`t`) of a string item (`si`) must be joined together
    return [
        "".join(
            text_element.text or ""
            for text_element in string_item.iter(f"{_SPREADSHEET_ML_NS}t")
        )
        for string_item in root.iterfind(f"{_SPREADSHEET_ML_NS}si")
    ]


def _find_first_worksheet_path(archive: zipfile.ZipFile) -> str:
    filenames = archive.namelist()
    if _WORKBOOK_PATH not in filenames or _WORKBOOK_RELS_PATH not in filenames:
        return _FALLBACK_WORKSHEET_PATH

    with archive.open(_WORKBOOK_PATH) as workbook_file:
        workbook = ET.parse(workbook_file).getroot()
    first_sheet = next(workbook.iter(f"{_SPREADSHEET_ML_NS}sheet"), None)
    if first_sheet is None:
        return _FALLBACK_WORKSHEET_PATH
    relationship_id = first_sheet.get(f"{_DOC_RELS_NS}id")

    with archive.open(_WORKBOOK_RELS_PATH) as rels_file:
        relationships = ET.parse(rels_file).getroot()
    for relationship in relationships.iterfind(f"{_PACKAGE_RELS_NS}Relationship"):
        if relationship.get("Id") == relationship_id:
            target = relationship.get("Target", "")
            # Targets are relative to the folder of the workbook, unless absolute
            return target.lstrip("/") if target.startswith("/") else f"xl/{target}"
    return _FALLBACK_WORKSHEET_PATH


def _column_index(cell_reference: str | None, *, default: int) -> int:
    match = _CELL_REFERENCE_REGEX.match(cell_reference or "")
    if not match:
        return default
    index = 0
    for character in match.group(1):
        index = index * 26 + (ord(character) - ord("A") + 1)
    return index - 1


def _cell_value(cell_element: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell_element.get("t", "n")
    if cell_type == "inlineStr":
        inline_string = cell_element.find(f"{_SPREADSHEET_ML_NS}is")
        if inline_string is None:
            return ""
        return "".join(
            text_element.text or ""
            for text_element in inline_string.iter(f"{_SPREADSHEET_ML_NS}t")
        )

    value_element = cell_element.find(f"{_SPREADSHEET_ML_NS}v")
    value = (value_element.text or "") if value_element is not None else ""
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError):
            return ""
    if cell_type == "b":
        return "TRUE" if value == "1" else "FALSE"
    # Numbers that happen to be integral are written with a trailing `.0` by some
    # programs, which would e.g. turn a card number into an invalid one
    return _INTEGRAL_FLOAT_REGEX.sub(r"\1", value)
