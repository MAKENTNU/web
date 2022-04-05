from typing import Type, Union

from django import template
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q

from users.models import User

register = template.Library()


@register.filter
def has_any_permissions(user: User):
    return (
            Permission.objects.filter(Q(group__user=user) | Q(user=user)).exists()
            or user.is_superuser
    )


@register.filter
def has_any_permissions_for(user: User, model__or__app_and_model: Union[Type[models.Model], str]):
    """
    :param user: the user to check permissions for
    :param model__or__app_and_model: either a model type, a string with the name of a uniquely named model,
                                     or a string of the format "{app_label}.{model_name}"
    """
    if not isinstance(model__or__app_and_model, str) and not isinstance(model__or__app_and_model, type(models.Model)):
        raise ValueError(f"Expected an instance of {str} or {type(models.Model)}, but got '{model__or__app_and_model}'")

    if user.is_anonymous:
        return False

    if isinstance(model__or__app_and_model, str):
        if "." in model__or__app_and_model:
            app_label, model_name = model__or__app_and_model.split(".", maxsplit=1)
            model = ContentType.objects.get_by_natural_key(app_label, model_name).model_class()
        else:
            model_name = model__or__app_and_model.lower()
            model = ContentType.objects.get(model=model_name).model_class()
    else:
        model = model__or__app_and_model

    return user.has_any_permissions_for(model)
