from users.models import User
from django.utils.datetime_safe import datetime

from make_queue.fields import MachineTypeField
from make_queue.models.models import Machine, Reservation


class MachineType:
    regex = "([0-9]+)"

    def to_python(self, value):
        return MachineTypeField.get_machine_type(int(value))

    def to_url(self, machine_type):
        if type(machine_type) is list and machine_type:
            return machine_type[0].id
        return machine_type.id


class SpecificMachine:
    regex = "([0-9]+)"

    def to_python(self, value):
        try:
            return Machine.objects.get(pk=int(value))
        except Machine.DoesNotExist:
            raise ValueError("No machine for that key")

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
        try:
            return Reservation.objects.get(pk=int(value))
        except Reservation.DoesNotExist:
            raise ValueError("No reservation for that key")

    def to_url(self, reservation):
        return str(reservation.pk)


class UserByUsername:
    regex = "([-0-9A-Za-z.]*)"

    def to_python(self, value):
        try:
            return User.objects.get(username=value)
        except User.DoesNotExist:
            raise ValueError("No user with that username")

    def to_url(self, user):
        return user.username
