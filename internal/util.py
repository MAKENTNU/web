def date_to_term(date):
    """
    Finds the term based on the given term. If the date is before June, then it is the spring term ("V").
    If the date is in June, July or before the 20th of August, it is the summer term/vacation ("S"). Else, the term
    is the fall term ("H").

    :return: A three character long string consisting of the two last digits of the year and a letter for the term.
    """
    term = "H"
    if date.month < 6:
        term = "V"
    elif date.month < 8 or date.month == 8 and date.day < 20:
        term = "S"
    return f"{term}{date.year % 100}"
