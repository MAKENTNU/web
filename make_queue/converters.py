from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.datetime_safe import datetime

from make_queue.models import Machine


class MachineType:
    regex = "(" + "|".join(machine.literal.replace("-", "\-") for machine in Machine.__subclasses__()) + ")"

    def to_python(self, value):
        return Machine.get_subclass(value)

    def to_url(self, machine_class):
        return machine_class.literal


class MachineTypeSpecific:
    regex = MachineType.regex + "/" + "([0-9]+)"

    def to_python(self, value):
        return MachineType().to_python(value.split("/")[0]).objects.get(pk=int(value.split("/")[1]))

    def to_url(self, machine):
        return MachineType().to_url(machine.__class__) + "/" + str(machine.pk)


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
    regex = Date.regex + "([0-9]{4}/([1-9]|1[0-2])/([1-9]|[1-2][0-9]|3[01])/([01][0-9]|2[0-3]):([0-5][0-9]))"

    def to_python(self, value):
        return datetime.strptime(value, "%Y/%m/%d/%H:%M")

    def to_url(self, date):
        return date.strftime(date, "%Y/%m/%d/%H:%M")



class MachineReservation:
    regex = MachineTypeSpecific.regex + "/([0-9]+)"

    def to_python(self, value):
        return MachineTypeSpecific().to_python("/".join(value.split("/")[:-1])).get_reservation_set().get(
            pk=int(value.split("/")[-1]))

    def to_url(self, reservation):
        return MachineTypeSpecific().to_url(reservation.get_machine()) + "/" + str(reservation.pk)


class UserByUsername:
    regex = "(" + "|".join(user.username.replace("-", "\-") for user in User.objects.all()) + ")"

    def to_python(self, value):
        return get_object_or_404(User, username=value)

    def to_url(self, user):
        return user.username
