from datetime import time

from django.contrib.auth.models import User
from django.db import models
from ckeditor.fields import RichTextField
from django.utils import timezone


class Skill(models.Model):
    level_choices = (
        (1, "Nybegynner"),
        (2, "Viderekommen"),
        (3, "Ekspert"),
    )
    title = models.CharField(max_length=100, verbose_name="Ferdighet")
    skill_level = models.IntegerField(choices=level_choices)


class Profile(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    card_id = models.CharField(max_length=100, verbose_name="Kortnummer")
    skill = models.ManyToManyField(Skill)
    # TODO: imagefield
