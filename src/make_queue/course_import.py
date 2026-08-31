"""
Importing of 3D printer course registrations from a spreadsheet.

The columns of the spreadsheet are recognized by their header, which makes it possible
to import a file that was previously exported from the course registration list.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from make_queue.models.course import CoursePermission, Printer3DCourse
from util.spreadsheet_utils import excel_serial_to_date

# The columns that can be imported, mapped to the headers that are recognized as them.
# The headers are compared after having been lowercased and stripped of everything but
# letters and digits
COLUMN_HEADER_ALIASES = {
    "name": (
        "name",
        "fullname",
        "navn",
        "fulltnavn",
        "coursename",
        "participant",
        "deltaker",
    ),
    "username": ("username", "user", "ntnuusername", "brukernavn", "ntnubrukernavn"),
    "card_number": ("cardnumber", "card", "kortnummer", "kort", "kortnr"),
    "date": ("date", "coursedate", "dato", "kursdato"),
}
# The order of the columns of a file without a recognizable header row, which is the
# same order as the columns of the exported course registration list
POSITIONAL_COLUMNS = ("name", "username", "card_number", "date")

DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y")

# Importing more rows than this is far more likely to be a mistake than intentional,
# and would in any case time out the request
MAX_NUM_ROWS = 2000


class CourseImportError(Exception):
    """Raised when the contents of a file cannot be interpreted as registrations."""


@dataclass(frozen=True)
class ImportedRow:
    """A single row of a spreadsheet, mapped to the fields of a registration."""

    line_number: int
    name: str = ""
    username: str = ""
    card_number: str = ""
    date_string: str = ""

    @property
    def display_name(self) -> str:
        return self.name or self.username or str(_("(no name)"))


@dataclass(frozen=True)
class RowOutcome:
    """The result of importing a single row."""

    row: ImportedRow
    message: str


@dataclass
class ImportResult:
    created: list[RowOutcome] = field(default_factory=list)
    skipped: list[RowOutcome] = field(default_factory=list)
    failed: list[RowOutcome] = field(default_factory=list)
    # Whether the created registrations were actually written to the database
    committed: bool = True

    @property
    def num_read(self) -> int:
        return len(self.created) + len(self.skipped) + len(self.failed)


def parse_rows(rows: list[list[str]]) -> list[ImportedRow]:
    """
    Map the rows of a spreadsheet to the fields of a course registration.

    :param rows: The rows of the spreadsheet, as returned by
                 :func:`util.spreadsheet_utils.read_rows`
    :return: One :class:`ImportedRow` per non-empty row
    :raises CourseImportError: If the file is empty, too long, or has no username column
    """
    if not rows:
        raise CourseImportError(_("The file is empty."))

    columns = _match_header_row(rows[0])
    if columns is None:
        columns = _positional_columns(len(rows[0]))
        data_rows = list(enumerate(rows, start=1))
    else:
        data_rows = list(enumerate(rows[1:], start=2))

    if "username" not in columns.values():
        raise CourseImportError(
            _(
                "Found no column with usernames. Name one of the columns"
                " “username” (or “brukernavn”), or remove the header row."
            )
        )
    if len(data_rows) > MAX_NUM_ROWS:
        raise CourseImportError(
            _(
                "The file has %(num_rows)d rows, but at most %(max_num_rows)d can be"
                " imported at a time."
            )
            % {"num_rows": len(data_rows), "max_num_rows": MAX_NUM_ROWS}
        )

    imported_rows = []
    for line_number, row in data_rows:
        if not any(row):
            continue
        values = {
            column: row[index].strip()
            for index, column in columns.items()
            if index < len(row)
        }
        imported_rows.append(
            ImportedRow(
                line_number=line_number,
                name=values.get("name", ""),
                username=values.get("username", ""),
                card_number=values.get("card_number", ""),
                date_string=values.get("date", ""),
            )
        )

    if not imported_rows:
        raise CourseImportError(_("The file contains no rows with data."))
    return imported_rows


def parse_date(date_string: str) -> date | None:
    """Parse a date written in one of the common formats, or as an Excel serial."""
    date_string = date_string.strip()
    if not date_string:
        return None
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(date_string, date_format).date()
        except ValueError:
            continue
    return excel_serial_to_date(date_string)


@transaction.atomic
def import_registrations(
    imported_rows: list[ImportedRow],
    *,
    default_date: date,
    status: str,
    course_permissions: list[CoursePermission],
    skip_already_registered: bool = True,
    import_valid_rows_only: bool = False,
) -> ImportResult:
    """
    Create a course registration per row, inside a single transaction.

    Unless ``import_valid_rows_only`` is set, the whole import is rolled back if any of
    the rows are invalid, which prevents ending up with a half-imported file.

    :param imported_rows: The rows to import, as returned by :func:`parse_rows`
    :param default_date: The course date to use for rows without a date of their own
    :param status: The registration status to give all the created registrations
    :param course_permissions: The permissions to give all the created registrations
    :param skip_already_registered: Whether an already registered username should be
                                    skipped instead of counted as an error
    :param import_valid_rows_only: Whether the valid rows should be created even if
                                   some of the rows are invalid
    :return: The outcome of each of the rows
    """
    # Imported here to prevent a circular import
    from make_queue.forms.course import Printer3DCourseForm

    result = ImportResult()
    existing_usernames = set(
        Printer3DCourse.objects.exclude(username="").values_list("username", flat=True)
    )
    usernames_in_file = set()

    for row in imported_rows:
        username = row.username.lower()
        if not username:
            result.failed.append(RowOutcome(row, str(_("Missing username"))))
            continue
        if username in usernames_in_file:
            message = _("The username appears multiple times in the file")
            result.failed.append(RowOutcome(row, str(message)))
            continue
        usernames_in_file.add(username)

        if username in existing_usernames:
            message = str(_("Already registered"))
            if skip_already_registered:
                result.skipped.append(RowOutcome(row, message))
            else:
                result.failed.append(RowOutcome(row, message))
            continue

        course_date = parse_date(row.date_string)
        if course_date is None and row.date_string:
            message = _("Invalid date: “%(date)s”") % {"date": row.date_string}
            result.failed.append(RowOutcome(row, str(message)))
            continue

        form = Printer3DCourseForm(
            data={
                "username": row.username,
                "name": row.name,
                "card_number": row.card_number,
                "date": course_date or default_date,
                "status": status,
                "course_permissions": [
                    permission.pk for permission in course_permissions
                ],
            }
        )
        if not form.is_valid():
            result.failed.append(RowOutcome(row, _format_form_errors(form)))
            continue

        form.save()
        result.created.append(RowOutcome(row, str(_("Registered"))))

    if result.failed and not import_valid_rows_only:
        # Roll back, so that a file with errors in it is either imported in full or
        # not at all
        transaction.set_rollback(True)
        result.committed = False
    return result


def _match_header_row(row: list[str]) -> dict[int, str] | None:
    """Map the index of each recognized header to its column, or ``None`` if no
    header was recognized."""
    columns = {}
    for index, header in enumerate(row):
        normalized_header = "".join(
            character for character in header.lower() if character.isalnum()
        )
        for column, aliases in COLUMN_HEADER_ALIASES.items():
            if normalized_header in aliases and column not in columns.values():
                columns[index] = column
                break
    return columns or None


def _positional_columns(num_columns: int) -> dict[int, str]:
    # A file with a single column is far more useful as a list of usernames than as a
    # list of names, which cannot be registered on their own
    if num_columns <= 1:
        return {0: "username"}
    return dict(enumerate(POSITIONAL_COLUMNS[:num_columns]))


def _format_form_errors(form) -> str:
    return " ".join(
        f"{form.fields[field_name].label or field_name}: {' '.join(errors)}"
        if field_name != "__all__"
        else " ".join(errors)
        for field_name, errors in form.errors.items()
    )
