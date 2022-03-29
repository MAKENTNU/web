from abc import ABC

from django.db.models import Model


class SpecificObjectConverter(ABC):
    regex = r"([0-9]+)"

    model: Model

    def to_python(self, value):
        try:
            return self.model.objects.get(pk=int(value))
        except self.model.DoesNotExist:
            raise ValueError(f"Unable to find any {self.model._meta.object_name} for the PK '{value}'")

    def to_url(self, obj):
        if type(obj) is int:
            return str(obj)
        elif isinstance(obj, self.model):
            return str(obj.pk)
        else:
            raise ValueError(f"Unable to convert '{obj}' to be used in a URL")
