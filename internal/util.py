from datetime import date


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
