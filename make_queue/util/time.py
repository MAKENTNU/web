import pytz
from django.utils import timezone, translation
from django.utils.datetime_safe import datetime
from django.utils.translation import ugettext
from calendar import day_name


def is_valid_week(year, week):
    """
    Checks if the given year and week is a valid combination. Uses 1-index weeks.

    :param year: The year to check
    :param week: The week to check
    :return: A boolean indicating if the given year and week is a valid combination
    """
    return 0 < week < 54 and year_and_week_to_monday(year, week).year == year


def year_and_week_to_monday(year, week):
    """
    Returns the a datetime object for the monday in the given week and year

    :param year: The year to get the date for
    :param week: The week to get the date for
    :return: The monday in the given week of the given year
    """
    return datetime.strptime(str(year) + " " + str(week) + " 1", "%Y %W %w")


def get_next_week(year, week, shift_direction):
    """
    Finds the next week and its year shifted in the given direction

    :param year: The current year
    :param week: The current week
    :param shift_direction: The direction to look for a week in 1 for forward and -1 for backwards
    :return: The next week with year
    """
    year, week = year + ((week + shift_direction) // 54), (week + shift_direction) % 54
    if is_valid_week(year, week):
        return year, week
    return get_next_week(year, week, shift_direction)


def date_to_local(date):
    """
    Converts a localized date to an unlocalized date in the default server timezone

    :param date: The date to convert to the default server timezone
    :return: The unlocalized date in the default server timezone
    """
    return timezone.localtime(date, timezone.get_default_timezone())


def local_to_date(date):
    """
    Converts an unlocalized date to a localized date by assuming it is in the default server timezone

    :param date: The date to localize
    :return: The localized date
    """
    return pytz.timezone(timezone.get_default_timezone_name()).localize(date)


def timedelta_to_hours(timedelta_obj):
    """
    Converts a timedelta object into a float indicating the number of hours the timedelta covers

    :param timedelta_obj: The timedelta object
    :return: The number of hours it covers
    """
    return timedelta_obj.days * 24 + timedelta_obj.seconds / 3600


def get_day_name(day_no, locale):
    """
    Gets the name of the given day [0, 6] in the given locale
    
    :param day_no: The day in the week in the range [0, 6], with Monday being 0
    :param locale: The language code
    :return: The name of the given day in the given locale
    """
    previous_lang = translation.get_language()
    translation.activate(locale)
    locale_day_name = ugettext(day_name[day_no])
    translation.activate(previous_lang)
    return locale_day_name
