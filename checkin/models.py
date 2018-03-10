from django.contrib.auth.models import User
from django.db import models
from ckeditor.fields import RichTextField
from django.utils import timezone


class Skill(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name="Ferdighet")

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL)
    card_id = models.CharField(max_length=100, verbose_name="Kortnummer")
    image = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True, verbose_name="Profilbilde")
    on_make = models.BooleanField(default=False, verbose_name="Innsjekkingsstatus")

    def __str__(self):
        if self.user:
            return self.user.username
        return "None"


class UserSkill(models.Model):
    level_choices = (
        (1, "Nybegynner"),
        (2, "Viderekommen"),
        (3, "Ekspert"),
    )
    profile = models.ForeignKey(Profile, null=True, on_delete=models.SET_NULL)
    skill = models.ForeignKey(Skill, null=True, on_delete=models.SET_NULL)
    skill_level = models.IntegerField(choices=level_choices)

    class Meta:
        ordering = (
            "skill__title",
        )

    def __str__(self):
        return str(self.profile) + " - " + str(self.skill)


class SuggestSkill(models.Model):
    creator = models.ForeignKey(Profile, related_name="suggestions", null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100, unique=True, verbose_name="Foreslått ferdighet")
    approved = models.BooleanField(default=False)
    voters = models.ManyToManyField(Profile, related_name="votes")

    def __str__(self):
        return str(self.title)

    class Meta:
        ordering = ('title',)
