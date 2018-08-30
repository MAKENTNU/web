from _datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from ckeditor.fields import RichTextField
from django.utils import timezone


class Skill(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name="Ferdighet")
    title_en = models.CharField(max_length=100, unique=True, default="", verbose_name="Skill (english)")
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    def __str__(self):
        return str(self.title_en)

    def locale_title(self, language_code):
        if language_code == "nb":
            return self.title
        return self.title_en


class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL)
    card_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Kortnummer")
    image = models.ImageField(upload_to='profile', blank=True, verbose_name="Profilbilde")
    on_make = models.BooleanField(default=False, verbose_name="Innsjekkingsstatus")
    last_checkin = models.DateTimeField(auto_now=True, verbose_name="Sist sjekket inn")

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
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
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
    title_en = models.CharField(max_length=100, unique=True, default="", verbose_name="Suggested skill")
    approved = models.BooleanField(default=False)
    voters = models.ManyToManyField(Profile, related_name="votes")
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    def __str__(self):
        return str(self.title_en)

    def locale_title(self, language_code):
        if language_code == "nb":
            return self.title
        return self.title_en

    class Meta:
        ordering = ('title',)


class RegisterProfile(models.Model):
    card_id = models.CharField(max_length=100, verbose_name="Kortnummer")
    last_scan = models.DateTimeField()

    def __str__(self):
        return str(self.card_id)
