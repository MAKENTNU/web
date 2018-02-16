import pytz
from django.utils import timezone


def date_to_local(date):
    return timezone.localtime(date, timezone.get_default_timezone())


def local_to_date(date):
    return pytz.timezone(timezone.get_default_timezone_name()).localize(date)