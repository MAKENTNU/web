from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


class Skill(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name=_("Title (Norwegian)"))
    title_en = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name=_("Title (English)"))
    image = models.ImageField(upload_to='skills', blank=True, verbose_name=_("Illustration image"))

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        if language_code == 'en':
            return self.title_en
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='profile',
    )
    image = models.ImageField(upload_to='profile', blank=True, verbose_name=_("Profile picture"))
    on_make = models.BooleanField(default=False, verbose_name=_("Checked in"))
    last_checkin = models.DateTimeField(auto_now=True, verbose_name=_("Last checked in"))

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
        related_name='user_skills',
    )
    skill = models.ForeignKey(
        to=Skill,
        on_delete=models.CASCADE,
        related_name='user_skills',
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
        related_name='skill_suggestions',
    )
    title = models.CharField(max_length=100, unique=True, verbose_name=_("Title (Norwegian)"))
    title_en = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name=_("Title (English)"))
    voters = models.ManyToManyField(
        to=Profile,
        related_name='skill_suggestions_voted_for',
    )
    image = models.ImageField(upload_to="skills", blank=True, verbose_name=_("Illustration image"))

    class Meta:
        ordering = ('title',)
        permissions = (
            ('can_force_suggestion', "Can force suggestion"),
        )

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        if language_code == 'en':
            return self.title_en
        return self.title


class RegisterProfile(models.Model):
    card_id = models.CharField(max_length=100, verbose_name=_("Card number"))
    last_scan = models.DateTimeField()

    def __str__(self):
        return self.card_id
