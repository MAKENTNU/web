from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from groups.models import Committee
from internal.util import date_to_term


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

    def on_create(self):
        self.email = self.user.email
        self.save()

        for property_name, value in MemberProperty.name_choices:
            # All members will be registered on the website when added to the members list
            MemberProperty.objects.create(name=property_name, value=property_name == "Website", member=self)

        # Want to add user to committees on creation
        for committee in self.committees.all():
            committee.group.user_set.add(self.user)

        # Add
        self.toggle_membership(True)

        return self

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
        self.toggle_membership(self.quit)
        self.quit = not self.quit

    def toggle_membership(self, membership_state):
        """
        Toggle membership by removing/adding the member to the MAKE group (if it exists)
        :param membership_state: True if the user should be a member of MAKE and false otherwise
        """
        make = Group.objects.filter(name="MAKE")
        if make.exists():
            if membership_state:
                make.first().user_set.add(self.user)
            else:
                make.first().user_set.discard(self.user)

    def __str__(self):
        return self.user.get_full_name()


@receiver(post_save, sender=Member)
def update_user_groups(sender, instance, created, updated_fields=None, **kwargs):
    if created:
        instance.on_create()
    else:
        # TODO: Update user groups if committees have changed
        pass


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
