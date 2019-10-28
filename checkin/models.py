from django.contrib.auth.models import User
from django.db import models


class Skill(models.Model):
    """Skill with image

    :var title: Skill name in Norwegian
    :var title_en: Skill name in English
    :var image: Skill image

    :func __str__: returns skill name
    :func locale_title(language_code): returns skill name in correct language
    """
    title = models.CharField(max_length=100, unique=True, verbose_name="Ferdighet")
    title_en = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Skill (english)")
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        """Returns skill name in correct language.

        Only 'nb' is recognised, everything else will return the english skill name.

        :param language_code: Two letter string with language code
        :return: skill name in correct language

        """

        if language_code == "nb":
            return self.title
        return self.title_en


class Profile(models.Model):
    """Profile model

    :var user: User model
    :var image: Profile picture
    :var on_make: boolean, if at Makerverkstedet
    :var last_checkin: DateTimeField, last time at Makerverkstedet

    :func __str__: returns username or 'None'
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
    """Model for user's skill

    :var profile: Profile model
    :var skill: skill model
    :var skill_level: Three levels, 1=beginner, 3=expert

    :func __str__: returns "[username] - [skill]"
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
    """Model for suggested skill

    :var creator: Profile model of the suggestion holder
    :var title: Suggested skill in Norwegian
    :var title_en: Suggested skill in English
    :var voters: Profile model of who has voted for suggested skill.
    :var image: Skill image

    :func __str__: returns suggested skill in Norwegian
    :func locale_title(language_code): returns suggested skill in correct language
    """
    creator = models.ForeignKey(Profile, related_name="suggestions", null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100, unique=True, verbose_name="Foreslått ferdighet")
    title_en = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Suggested skill")
    voters = models.ManyToManyField(Profile, related_name="votes")
    image = models.ImageField(upload_to='skills', blank=True, verbose_name="Ferdighetbilde")

    def __str__(self):
        return self.title

    def locale_title(self, language_code):
        if language_code == "nb":
            return self.title
        return self.title_en

    class Meta:
        ordering = ('title',)
        permissions = (
            ("can_force_suggestion", "Can force suggestion"),
        )


class RegisterProfile(models.Model):
    """Model for registrating profile

        :var card_id: Charfield with student card number.
        :var last_scan: DateTimeField with time of last scan

        :func __str__: returns card_id

    """

    card_id = models.CharField(max_length=100, verbose_name="Kortnummer")
    last_scan = models.DateTimeField()

    def __str__(self):
        return str(self.card_id)
