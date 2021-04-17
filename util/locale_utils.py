from datetime import datetime, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.formats import date_format
from django.utils.timezone import make_aware
from django.utils.translation import ngettext_lazy


DEFAULT_TIMEZONE = timezone.get_default_timezone()
# Code based on https://github.com/django/django/blob/9736596bce4f711ccf2914284938d85748838c94/django/utils/timesince.py#L8-L15
TIME_STRINGS = {
    'year': ngettext_lazy("%(num)d year", "%(num)d years", 'num'),
    'month': ngettext_lazy("%(num)d month", "%(num)d months", 'num'),
    'week': ngettext_lazy("%(num)d week", "%(num)d weeks", 'num'),
    'day': ngettext_lazy("%(num)d day", "%(num)d days", 'num'),
    'hour': ngettext_lazy("%(num)d hour", "%(num)d hours", 'num'),
    'minute': ngettext_lazy("%(num)d minute", "%(num)d minutes", 'num'),
}


def parse_datetime_localized(value):
    return make_aware(parse_datetime(value))


def attempt_as_local(value):
    if (isinstance(value, datetime)
            # Each timezone has its own `tzinfo` subclass
            and type(value.tzinfo) is not type(DEFAULT_TIMEZONE)):
        try:
            value = value.astimezone(DEFAULT_TIMEZONE)
        except OSError:
            # `value` is probably either too low (Unix epoch or before) or too high (around year 3000 or higher, it seems)
            pass
    return value


def _date_format(value, format_):
    value = attempt_as_local(value)
    return date_format(value, format_)


def short_date_format(value):
    return _date_format(value, 'SHORT_DATE_FORMAT')


def short_datetime_format(value):
    return _date_format(value, 'SHORT_DATETIME_FORMAT')


def long_date_format(value):
    return _date_format(value, 'DATE_FORMAT')


def long_datetime_format(value):
    return _date_format(value, 'DATETIME_FORMAT')


def time_format(value):
    return _date_format(value, 'TIME_FORMAT')


def iso_date_format(value):
    if isinstance(value, datetime):
        value = attempt_as_local(value).date()
    return value.isoformat()


def iso_datetime_format(value):
    value = attempt_as_local(value)
    return value.isoformat()


def exact_weekday_to_day_name(exact_weekday: float):
    from make_queue.models.reservation import ReservationRule  # avoids circular imports

    truncated_and_wrapped_weekday = int(exact_weekday - 1) % 7 + 1
    return ReservationRule.DAY_INDEX_TO_NAME[truncated_and_wrapped_weekday]


def year_and_week_to_monday(year, week):
    """
    Returns the a datetime object for the monday in the given week and year.

    :param year: The year to get the date for
    :param week: The week to get the date for
    :return: The monday in the given week of the given year
    """
    return datetime.strptime(f"{year:04d} {week:02d} 1", "%G %V %w")


def timedelta_to_hours(timedelta_obj: timedelta):
    """
    Converts a timedelta object into a float indicating the number of hours the timedelta covers.

    :param timedelta_obj: The timedelta object
    :return: The number of hours it covers
    """
    return timedelta_obj.days * 24 + timedelta_obj.seconds / (60 * 60)
