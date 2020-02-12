from django.contrib.auth.models import User
from django.db import models


class Skill(models.Model):
    """Skill with image"""
    title = models.CharField(max_length=100, unique=True, verbose_name="Ferdighet")
    title_en = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Skill (english)")
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        """
        Finds the title of the skill in Norwegian Bokmål or English,
        defaulting to English for all other language codes.

        :param language_code: A string representing an ISO 639-1 language code
        :return: Skill name in given language
        """
        if language_code == "nb":
            return self.title
        return self.title_en


class Profile(models.Model):
    """
    A model for user profiles, storing the status of the their last visit to Makerverkstedet

    :var user: The user to which this profile belongs
    :var image: Profile picture
    :var on_make: Indicates if the user is at Makerverkstedet
    :var last_checkin: Last time at Makerverkstedet
    """
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL)
    image = models.ImageField(upload_to='profile', blank=True, verbose_name="Profilbilde")
    on_make = models.BooleanField(default=False, verbose_name="Innsjekkingsstatus")
    last_checkin = models.DateTimeField(auto_now=True, verbose_name="Sist sjekket inn")

    def __str__(self):
        if self.user:
            return self.user.username
        return "None"


class UserSkill(models.Model):
    """
    A model for indicating a user's skill level

    :var profile: The profile of the user
    :var skill: The skill which the object indicates the user's skill
    :var skill_level: The user's skill level, can be one of three levels: "beginner", "intermediate" or "expert"
    """
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
    """
    Model for suggested skill, keeping track of suggestion creator and voters

    :var creator: Profile model of the suggestion holder
    :var title: Suggested skill in Norwegian
    :var title_en: Suggested skill in English
    :var voters: Profile model of who has voted for suggested skill.
    :var image: Skill image
    """
    creator = models.ForeignKey(Profile, related_name="suggestions", null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100, unique=True, verbose_name="Foreslått ferdighet")
    title_en = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Suggested skill")
    voters = models.ManyToManyField(Profile, related_name="votes")
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        """
        Finds the title of the skill in Norwegian Bokmål or English,
        defaulting to English for all other language codes.

        :param language_code: A string representing an ISO 639-1 language code
        :return: Skill name in given language
        """
        if language_code == "nb":
            return self.title
        return self.title_en

    class Meta:
        ordering = ('title',)
        permissions = (
            ("can_force_suggestion", "Can force suggestion"),
        )


class RegisterProfile(models.Model):
    """
    Model for registrating profile, storing card id and time of last scan

    :var card_id: Student card number.
    :var last_scan: Time of last scan
    """

    card_id = models.CharField(max_length=100, verbose_name="Kortnummer")
    last_scan = models.DateTimeField()

    def __str__(self):
        return str(self.card_id)
