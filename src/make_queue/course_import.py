"""
Importing of 3D printer course registrations from a spreadsheet.

The file must have exactly the columns of ``COLUMNS``, in that order, named by a
header row. Accepting only one format keeps both the code and the error messages
short, and makes it unambiguous what a file that is rejected has to look like.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from make_queue.models.course import CoursePermission, Printer3DCourse
from util.spreadsheet_utils import excel_serial_to_date

# The columns of an importable file, in the order they must appear in. Only the
# username is required to have a value; the rest of the cells may be left empty
COLUMNS = ("username", "name", "card_number", "date")
HEADER_ROW = ", ".join(COLUMNS)

DATE_FORMAT = "%Y-%m-%d"

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
    # The date the registration got, which is `None` for a row that was not far enough
    # along to have one worked out
    course_date: date | None = None
    # Whether the date above came from the default, because the row had none of its own
    date_from_default: bool = False


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
    :raises CourseImportError: If the file is empty, too long, or has the wrong columns
    """
    if not rows:
        raise CourseImportError(_("The file is empty."))

    header = tuple(column.strip().lower() for column in rows[0])
    if header != COLUMNS:
        raise CourseImportError(
            _("The first row of the file must name the columns: %(header_row)s")
            % {"header_row": HEADER_ROW}
        )

    data_rows = list(enumerate(rows[1:], start=2))
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
        username, name, card_number, date_string = (cell.strip() for cell in row)
        imported_rows.append(
            ImportedRow(
                line_number=line_number,
                name=name,
                username=username,
                card_number=card_number,
                date_string=date_string,
            )
        )

    if not imported_rows:
        raise CourseImportError(_("The file contains no rows with data."))
    return imported_rows


def parse_date(date_string: str) -> date | None:
    """
    Parse a date written on the form ``YYYY-MM-DD``.

    A date typed into a spreadsheet is stored as a serial number rather than as text,
    so those are converted as well - it is the same format, just written by the file
    format instead of by the user.
    """
    date_string = date_string.strip()
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, DATE_FORMAT).date()
    except ValueError:
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
    dry_run: bool = False,
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
    :param dry_run: Whether to roll back afterwards no matter the outcome, which makes
                    it possible to show exactly what an import would do before doing it
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

        if not row.card_number:
            result.failed.append(RowOutcome(row, str(_("Missing card number"))))
            continue

        course_date = parse_date(row.date_string)
        if course_date is None and row.date_string:
            message = _("Invalid date: “%(date)s”") % {"date": row.date_string}
            result.failed.append(RowOutcome(row, str(message)))
            continue
        date_from_default = course_date is None
        course_date = course_date or default_date

        form = Printer3DCourseForm(
            data={
                "username": row.username,
                "name": row.name,
                "card_number": row.card_number,
                "date": course_date,
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
        result.created.append(
            RowOutcome(
                row,
                str(_("Registered")),
                course_date=course_date,
                date_from_default=date_from_default,
            )
        )

    if dry_run or (result.failed and not import_valid_rows_only):
        # Roll back, so that a file with errors in it is either imported in full or not
        # at all - and so that a dry run leaves nothing behind
        transaction.set_rollback(True)
        result.committed = False
    return result


def _format_form_errors(form) -> str:
    return " ".join(
        f"{form.fields[field_name].label or field_name}: {' '.join(errors)}"
        if field_name != "__all__"
        else " ".join(errors)
        for field_name, errors in form.errors.items()
    )
