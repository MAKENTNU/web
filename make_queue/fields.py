from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from card.models import Card
from make_queue.models.course import Printer3DCourse
from web.widgets import SemanticSearchableChoiceInput


class MachineType:

    def __init__(self, id, name, cannot_use_text, can_user_use, has_stream):
        self.id = id
        self.name = name
        self.cannot_use_text = cannot_use_text
        self.can_user_use_func = can_user_use
        self.has_stream = has_stream

    def can_user_use(self, user):
        return self.can_user_use_func(user)


def can_use_3d_printer(user):
    if not user.is_authenticated:
        return False
    if Printer3DCourse.objects.filter(user=user).exists():
        return True
    if Printer3DCourse.objects.filter(username=user.username).exists():
        course_registration = Printer3DCourse.objects.get(username=user.username)
        course_registration.user = user
        course_registration.save()
        Card.update_or_create(user, course_registration.card_number)
        return True
    return False


class MachineTypeField(models.IntegerField):
    description = "A machine type"
    verbose_name = _("Select machine type")

    # ID, name, cannot use text
    possible_machine_types = (
        MachineType(
            1,
            _("3D-printers"),
            _("You must have completed a 3D printer course to reserve the printers. If you "
              "have taken the course, but don't have access, contact 3dprint@makentnu.no"),
            can_use_3d_printer,
            True,
        ),
        MachineType(
            2,
            _("Sewing machines"),
            "",
            lambda user: user.is_authenticated,
            False,
        ),
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
            ),
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


class MachineTypeForm(forms.TypedChoiceField):
    widget = SemanticSearchableChoiceInput(prompt_text=MachineTypeField.verbose_name)

    def __init__(self, *args, **kwargs):
        kwargs.update({"coerce": self.coerce})
        super().__init__(*args, **kwargs)

    @staticmethod
    def coerce(value):
        return MachineTypeField.get_machine_type(int(value))

    def prepare_value(self, value):
        if type(value) is MachineType:
            return value.id
        return value
