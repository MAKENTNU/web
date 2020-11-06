from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


class Skill(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name="Ferdighet")
    title_en = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name="Skill (english)")
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        if language_code == "nb":
            return self.title
        return self.title_en


class Profile(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
    )
    image = models.ImageField(upload_to='profile', blank=True, verbose_name="Profilbilde")
    on_make = models.BooleanField(default=False, verbose_name="Innsjekkingsstatus")
    last_checkin = models.DateTimeField(auto_now=True, verbose_name="Sist sjekket inn")

    def __str__(self):
        if self.user:
            return self.user.username
        return "None"


class UserSkill(models.Model):
    class Level(models.IntegerChoices):
        BEGINNER = 1, _("Beginner")
        EXPERIENCED = 2, _("Experienced")
        EXPERT = 3, _("Expert")

    profile = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
    )
    skill = models.ForeignKey(
        to=Skill,
        on_delete=models.CASCADE,
    )
    skill_level = models.IntegerField(choices=Level.choices)

    class Meta:
        ordering = ('skill__title',)

    def __str__(self):
        return f"{self.profile} - {self.skill}"


class SuggestSkill(models.Model):
    creator = models.ForeignKey(
        to=Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='suggestions',
    )
    title = models.CharField(max_length=100, unique=True, verbose_name="Foreslått ferdighet")
    title_en = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name="Suggested skill")
    voters = models.ManyToManyField(
        to=Profile,
        related_name='votes',
    )
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    class Meta:
        ordering = ('title',)
        permissions = (
            ("can_force_suggestion", "Can force suggestion"),
        )

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        if language_code == "nb":
            return self.title
        return self.title_en


class RegisterProfile(models.Model):
    card_id = models.CharField(max_length=100, verbose_name="Kortnummer")
    last_scan = models.DateTimeField()

    def __str__(self):
        return str(self.card_id)
