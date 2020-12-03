from datetime import date
from typing import Any, Callable

from django.template import Library
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
from django.utils.formats import get_format
from django.utils.translation import get_language

from util.locale_utils import long_date_format, long_datetime_format, short_date_format, short_datetime_format, time_format

register = Library()


def _format_helper(value, format_func: Callable[[Any], str]):
    if value in {None, ""}:
        return ""
    return format_func(value)


# The following datetime filters don't require `expects_localtime=True`,
# because they deal with both naive and aware datetimes properly

@register.filter
def short_date(value):
    return _format_helper(value, short_date_format)


@register.filter
def short_datetime(value):
    return _format_helper(value, short_datetime_format)


@register.filter
def long_date(value):
    return _format_helper(value, long_date_format)


@register.filter
def long_datetime(value):
    return _format_helper(value, long_datetime_format)


@register.filter
def only_time(value):
    return _format_helper(value, time_format)


# The following format strings are copied from Django's default format strings

LONG_DATETIME_YEAR_PARTS = {
    'nb': " Y",
    'en': ", Y",
}

SHORT_YEAR_WISE_DATES = {
    'nb': ("d b", "d b Y"),
    'en': ("M d", "M d, Y"),
}

LONG_YEAR_WISE_DATES = {
    'nb': ("j. F", "j. F Y"),
    'en': ("N j", "N j, Y"),
}


@register.filter(expects_localtime=True)
def long_datetime_no_year(value):
    year_part = LONG_DATETIME_YEAR_PARTS[get_language()]
    datetime_format = get_format('DATETIME_FORMAT').replace(year_part, "")
    return date_filter(value, datetime_format)


@register.filter(expects_localtime=True)
def year_wise_short_date(value):
    same_year_format, different_year_format = SHORT_YEAR_WISE_DATES[get_language()]
    return _format_year_wise_date(value, same_year_format, different_year_format)


@register.filter(expects_localtime=True)
def year_wise_long_date(value):
    same_year_format, different_year_format = LONG_YEAR_WISE_DATES[get_language()]
    return _format_year_wise_date(value, same_year_format, different_year_format)


def _format_year_wise_date(value, same_year_format: str, different_year_format: str):
    date_format = None
    if isinstance(value, date):  # `datetime` objects are also `date` objects
        date_format = same_year_format if value.year == timezone.localdate().year else different_year_format
    return date_filter(value, date_format)