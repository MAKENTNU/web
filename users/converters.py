from .models import User


class SpecificUser:
    regex = r"([0-9]+)"

    def to_python(self, value):
        try:
            return User.objects.get(pk=int(value))
        except User.DoesNotExist:
            raise ValueError(f"Unable to find any user for the PK '{value}'")

    def to_url(self, obj):
        if type(obj) is int:
            return str(obj)
        elif isinstance(obj, User):
            return str(obj.pk)
        else:
            raise ValueError(f"Unable to convert '{obj}' to be used in a URL")
