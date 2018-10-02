from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import datetime

from make_queue.fields import MachineTypeField
from make_queue.models import Machine, Reservation


class MachineType:
    regex = "(" + "|".join(machine_type.name.replace("-", "\-") for machine_type in MachineTypeField.possible_machine_types) + ")"

    def to_python(self, value):
        return [machine_type for machine_type in MachineTypeField.possible_machine_types if machine_type.name == value]

    def to_url(self, machine_type):
        return machine_type.name


class SpecificMachine:
    regex = "([0-9]+)"

    def to_python(self, value):
        return Machine.objects.get(pk=int(value))

    def to_url(self, machine):
        return str(machine.pk)


class Year:
    regex = "([0-9]{4})"

    def to_python(self, value):
        return int(value)

    def to_url(self, year):
        return str(year)


class Week:
    regex = "([0-9]|[1-4][0-9]|5[0-3])"

    def to_python(self, value):
        return int(value)

    def to_url(self, week):
        return str(week)


class Date:
    regex = "([0-9]{4}/([1-9]|1[0-2])/([1-9]|[1-2][0-9]|3[01]))"

    def to_python(self, value):
        return datetime.strptime(value, "%Y/%m/%d")

    def to_url(self, date):
        return date.strftime(date, "%Y/%m/%d")


class DateTime:
    regex = "([0-9]{4}/([1-9]|1[0-2])/([1-9]|[1-2][0-9]|3[01])/([01][0-9]|2[0-3]):([0-5][0-9]))"

    def to_python(self, value):
        return datetime.strptime(value, "%Y/%m/%d/%H:%M")

    def to_url(self, date):
        return date.strftime(date, "%Y/%m/%d/%H:%M")


class MachineReservation:
    regex = "([0-9]+)"

    def to_python(self, value):
        return Reservation.objects.get(pk=int(value))

    def to_url(self, reservation):
        return str(reservation.pk)


class UserByUsername:
    regex = "([-0-9A-Za-z.]*)"

    def to_python(self, value):
        return get_object_or_404(User, username=value)

    def to_url(self, user):
        return user.username
