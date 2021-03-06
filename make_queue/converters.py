from users.models import User
from .models.models import Machine, MachineType, Reservation


class SpecificMachineType:
    regex = "([0-9]+)"

    def to_python(self, value):
        try:
            return MachineType.objects.get(pk=int(value))
        except MachineType.DoesNotExist:
            raise ValueError("No machine type for that key")

    def to_url(self, machine_type: MachineType):
        return str(machine_type.pk)


class SpecificMachine:
    regex = "([0-9]+)"

    def to_python(self, value):
        try:
            return Machine.objects.get(pk=int(value))
        except Machine.DoesNotExist:
            raise ValueError("No machine for that key")

    def to_url(self, machine: Machine):
        return str(machine.pk)


class Year:
    regex = "([0-9]{4})"

    def to_python(self, value):
        return int(value)

    def to_url(self, year: int):
        return str(year)


class Week:
    regex = "([0-9]|[1-4][0-9]|5[0-3])"

    def to_python(self, value):
        return int(value)

    def to_url(self, week: int):
        return str(week)


class MachineReservation:
    regex = "([0-9]+)"

    def to_python(self, value):
        try:
            return Reservation.objects.get(pk=int(value))
        except Reservation.DoesNotExist:
            raise ValueError("No reservation for that key")

    def to_url(self, reservation: Reservation):
        return str(reservation.pk)


class UserByUsername:
    regex = "([-0-9A-Za-z.]*)"

    def to_python(self, value):
        try:
            return User.objects.get(username=value)
        except User.DoesNotExist:
            raise ValueError("No user with that username")

    def to_url(self, user: User):
        return user.username
