from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User
from util.modelfields import CompressedImageField
from util.storage import OverwriteStorage, UploadToUtils


class Skill(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name=_("title (Norwegian)"))
    title_en = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name=_("title (English)"))
    image = CompressedImageField(upload_to=UploadToUtils.get_pk_prefixed_filename_func('skills'),
                                 blank=True, max_length=200, storage=OverwriteStorage(), verbose_name=_("illustration image"))

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        if language_code == 'en':
            return self.title_en
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    image = models.ImageField(upload_to=UploadToUtils.get_pk_prefixed_filename_func('profiles'),
                              blank=True, max_length=200, storage=OverwriteStorage(), verbose_name=_("profile picture"))
    on_make = models.BooleanField(default=False, verbose_name=_("checked in"))
    last_checkin = models.DateTimeField(auto_now=True, verbose_name=_("last checked in"))

    def __str__(self):
        return str(self.user)


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
    title = models.CharField(max_length=100, unique=True, verbose_name=_("title (Norwegian)"))
    title_en = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name=_("title (English)"))
    voters = models.ManyToManyField(
        to=Profile,
        related_name='skill_suggestions_voted_for',
    )
    image = CompressedImageField(upload_to=UploadToUtils.get_pk_prefixed_filename_func('skills/suggestions'),
                                 blank=True, max_length=200, storage=OverwriteStorage(), verbose_name=_("illustration image"))

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
    card_id = models.CharField(max_length=100, verbose_name=_("card number"))
    last_scan = models.DateTimeField()

    def __str__(self):
        return self.card_id
