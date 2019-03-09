from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from groups.models import Committee
from internal.util import date_to_term
from django.utils.translation import gettext_lazy as _


class Member(models.Model):
    class Meta:
        permissions = (
            ("is_internal", "Is a member of MAKE NTNU"),
            ("can_register_new_member", "Can register new member"),
            ("can_edit_group_membership", "Can edit the groups a member is part of, including (de)activation")
        )

    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, null=True)
    committees = models.ManyToManyField(Committee)
    role = models.CharField(max_length=64)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=32, default="")
    study_program = models.CharField(max_length=32, default="")
    card_number = models.CharField(max_length=32, default="")
    date_joined = models.DateField(default=timezone.datetime.now)
    date_quit = models.DateField(blank=True, null=True)
    reason_quit = models.TextField(max_length=256, default="")
    comment = models.TextField(max_length=256, default="")
    active = models.BooleanField(default=True)
    guidance_exemption = models.BooleanField(default=False)
    quit = models.BooleanField(default=False)
    retired = models.BooleanField(default=False)
    honorary_member = models.BooleanField(default=False)

    @classmethod
    def create(cls, *args, **kwargs):
        member = cls(*args, **kwargs)
        member.email = member.user.email
        member.save()
        for property_name, value in MemberProperty.name_choices:
            # All members will be registered on the website when added to the members list
            MemberProperty.objects.create(name=property_name, value=property_name == "Nettside", member=member)
        return member

    @property
    def term_joined(self):
        return date_to_term(self.date_joined)

    @property
    def term_quit(self):
        if self.date_quit is None:
            return None
        return date_to_term(self.date_quit)

    def toggle_quit(self, reason=""):
        if self.quit:
            for committee in self.committees.all():
                committee.group.user_set.add(self.user)
            self.date_quit = None
        else:
            for committee in self.committees.all():
                committee.group.user_set.discard(self.user)
            self.date_quit = timezone.now()

        self.reason_quit = reason
        self.quit = not self.quit


class MemberProperty(models.Model):
    name_choices = (
        (_("Drive"), "drive"),
        (_("Slack"), "slack"),
        (_("Google Calendar"), "calendar"),
        (_("Trello"), "trello"),
        (_("Email lists"), "email"),
        (_("Website"), "website")
    )

    name = models.fields.CharField(max_length=32, choices=name_choices)
    value = models.fields.BooleanField()
    member = models.ForeignKey(Member, models.CASCADE)
