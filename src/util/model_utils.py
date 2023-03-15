from django.db import models


# Code based on https://github.com/Uninett/Argus/blob/b00b7500e78148023d6b2e3afa87f71922190646/src/argus/util/utils.py#L4-L10
def duplicate(obj: models.Model, **set_attrs):
    obj_copy = obj._meta.model.objects.get(pk=obj.pk)
    obj_copy.pk = None
    for attr, value in set_attrs.items():
        setattr(obj_copy, attr, value)
    obj_copy.save()
    return obj_copy


class ComparisonType(models.TextChoices):
    EQ = "compare", "with"
    ADD = "add", "to"
    SUB = "subtract", "from"


def comparison_boilerplate(self, other, comparison_type: ComparisonType):
    """Performs various common boilerplate checks for comparison methods on models."""
    if not isinstance(other, type(self)):
        verb, preposition = comparison_type.value, comparison_type.label
        raise TypeError(f"Cannot {verb} '{type(other).__name__}' {preposition} {type(self).__name__}")
