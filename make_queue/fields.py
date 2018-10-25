from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from make_queue.models.course import Printer3DCourse
from web.widgets import SemanticChoiceInput


class MachineType:

    def __init__(self, id, name, cannot_use_text, can_user_use):
        self.id = id
        self.name = name
        self.cannot_use_text = cannot_use_text
        self.can_user_use_func = can_user_use

    def can_user_use(self, user):
        return self.can_user_use_func(user)


class MachineTypeForm(forms.TypedChoiceField):
    widget = SemanticChoiceInput

    def __init__(self, *args, **kwargs):
        kwargs.update({"coerce": self.coerce})
        super().__init__(*args, **kwargs)

    @staticmethod
    def coerce(value):
        return MachineTypeField.get_machine_type(int(value))


class MachineTypeField(models.IntegerField):
    description = "A machine type"

    # ID, name, cannot use text
    possible_machine_types = (
        MachineType(
            1,
            _("3D-printers"),
            _("You must have completed a 3D printer course to reserve the printers. If you "
              "have taken the course, but don't have access, contact 3dprint@makentnu.no"),
            lambda user: user.is_authenticated and Printer3DCourse.objects.filter(user=user).exists()
        ),
        MachineType(
            2,
            _("Sewing machines"),
            "",
            lambda user: user.is_authenticated
        )
    )

    @staticmethod
    def get_machine_type(id):
        types = list(filter(lambda y: y.id == id, MachineTypeField.possible_machine_types))
        if types:
            return types[0]
        return None

    def __init__(self, *args, **kwargs):
        kwargs.update({
            "choices": (
                (machine_type.id, machine_type.name) for machine_type in MachineTypeField.possible_machine_types
            )
        })
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return value
        if type(value) == MachineType:
            return value
        try:
            value = int(value)
            for machine_type in MachineTypeField.possible_machine_types:
                if machine_type.id == value:
                    return machine_type
        except (TypeError, ValueError):
            raise ValidationError("Not a valid type")
        raise ValidationError("Not a valid machine")

    def get_prep_value(self, value):
        if value is None:
            return value
        if type(value) is list:
            return value[0].id
        return value.id

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.get_machine_type(value)

    def formfield(self, **kwargs):
        defaults = {"choices_form_class": MachineTypeForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def value_to_string(self, obj):
        return obj.name

    def validate(self, value, model_instance):
        if type(value) != int:
            super(MachineTypeField, self).validate(self.get_prep_value(value), model_instance)
        else:
            super(MachineTypeField, self).validate(value, model_instance)
