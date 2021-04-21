from users.models import User
from util.url_utils import SpecificObjectConverter
from .models.machine import Machine, MachineType
from .models.reservation import Reservation


class SpecificMachineType(SpecificObjectConverter):
    model = MachineType


class SpecificMachine(SpecificObjectConverter):
    model = Machine


class SpecificReservation(SpecificObjectConverter):
    model = Reservation


class UserByUsername:
    regex = r"([-0-9A-Za-z.]*)"

    def to_python(self, value):
        try:
            return User.objects.get(username=value)
        except User.DoesNotExist:
            raise ValueError("No user with that username")

    def to_url(self, user: User):
        return user.username


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
