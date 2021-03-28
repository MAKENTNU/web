from datetime import date

from django.utils import timezone

from .validators import semester_string_regex


def date_to_semester(date_: date) -> str:
    """
    Finds the semester based on the provided date. If the date is before June, then it is the spring semester ("V").
    If the date is in June, July or before the 20th of August, it is the summer semester / vacation ("S").
    Otherwise, the semester is the fall semester ("H").

    :return: A three character long string consisting of the two last digits of the year and a letter for the semester.
    """
    semester = "H"
    if date_.month < 6:
        semester = "V"
    elif date_.month < 8 or date_.month == 8 and date_.day < 20:
        semester = "S"
    return f"{semester}{date_.year % 100}"


def semester_to_year(semester: str) -> float:
    """
    Converts ``semester`` from a string representation of a specific semester to a float representation.

    :param semester: a string in the format [V/H][year], where ``year`` is either the 2 last digits of a year or the full 4 digits.
                     For example "V17" or "H2017".
    :return: a float denoting the full year, with the decimal part representing the year half.
             For example ``2017.0`` (V17) or ``2017.5`` (H17).
    """
    regex_match = semester_string_regex.match(semester)
    if not regex_match:
        raise ValueError(f"'{semester}' is not a valid semester string")

    year_half, year_str = regex_match.groups()
    year = float(year_str)
    if len(year_str) == 2:
        current_year = timezone.now().year
        current_century = current_year - current_year % 100
        year += current_century
    if year_half.upper() == "H":
        year += 0.5
    return year


def year_to_semester(year: float) -> str:
    """
    Converts ``year`` from a float representation of a specific semester to a string representation.
    This function does the opposite of ``semester_to_year()``; see its documentation for more details.
    """
    if not 0 <= year <= 9999:
        raise ValueError(f"'{year}' is not a valid year")

    current_year = timezone.now().year
    same_century = year // 100 == current_year // 100
    year_str = int(year % 100) if same_century else int(year)
    year_half = "V" if year % 1 < 0.5 else "H"
    return f"{year_half}{year_str}"
