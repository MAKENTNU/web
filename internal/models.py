from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.urls import reverse
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

    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, null=True, verbose_name=_("User"))
    committees = models.ManyToManyField(Committee, blank=True, verbose_name=_("Committees"))
    role = models.CharField(max_length=64, blank=True, verbose_name=_("Role"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    phone_number = models.CharField(max_length=32, default="", blank=True, verbose_name=_("Phone number"))
    study_program = models.CharField(max_length=32, default="", blank=True, verbose_name=_("Study program"))
    card_number = models.CharField(max_length=32, default="", blank=True, verbose_name=_("Card number (EM)"))
    date_joined = models.DateField(default=timezone.datetime.now, verbose_name=_("Date joined"))
    date_quit = models.DateField(blank=True, null=True, verbose_name=_("Date quit"))
    reason_quit = models.TextField(max_length=256, default="", blank=True, verbose_name=_("Reason quit"))
    comment = models.TextField(max_length=256, default="", blank=True, verbose_name=_("Comment"))
    active = models.BooleanField(default=True, verbose_name=_("Is active"))
    guidance_exemption = models.BooleanField(default=False, verbose_name=_("Guidance exemption"))
    quit = models.BooleanField(default=False, verbose_name=_("Has quit"))
    retired = models.BooleanField(default=False, verbose_name=_("Retired"))
    honorary = models.BooleanField(default=False, verbose_name=_("Honorary"))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        is_creation = self.pk is None

        super().save(force_insert, force_update, using, update_fields)

        if is_creation:
            self.email = self.user.email

            # Setup all properties for new members
            for property_name, value in SystemAccess.name_choices:
                # All members will be registered on the website when added to the members list
                SystemAccess.objects.create(name=property_name, member=self,
                                            value=property_name == SystemAccess.WEBSITE)

            # Add user to the MAKE group
            self.toggle_membership(True)

    @property
    def term_joined(self):
        return date_to_term(self.date_joined)

    @property
    def term_quit(self):
        if self.date_quit is None:
            return None
        return date_to_term(self.date_quit)

    def toggle_quit(self, quit_state, reason="", date_quit=timezone.now()):
        """
        Perform all the actions to set a member as quit or undo this action
        :param quit_state: Indicates if the member has quit
        :param reason: The reason why the member has quit
        :param date_quit: The date the member quit
        """
        self.quit = quit_state
        if self.quit:
            self.date_quit = date_quit
        else:
            self.date_quit = None

        self.reason_quit = reason
        self.toggle_committee_membership(not quit_state)
        self.toggle_membership(not quit_state)

    def toggle_retirement(self, retirement_state):
        """
        Performs all the actions to set a member as retired or to undo this action
        :param retirement_state: Indicates if the member has retired
        """
        self.retired = retirement_state
        self.toggle_committee_membership(not retirement_state)
        self.toggle_membership(True)

    def toggle_committee_membership(self, membership_state):
        """
        Adds or removes the user to all the committees of its membership
        :param membership_state: Indicates if the member should be a part of the commitees
        """
        for committee in self.committees.all():
            if membership_state:
                committee.group.user_set.add(self.user)
            else:
                committee.group.user_set.remove(self.user)

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
                make.first().user_set.remove(self.user)

    def __str__(self):
        return self.user.get_full_name()


@receiver(m2m_changed, sender=Member.committees.through)
def member_update_user_groups(sender, instance, action="", pk_set=None, **kwargs):
    """
    Makes sure that the member is added/removed from the correct groups as its committee membership changes
    """
    if action == "pre_add":
        committees = Committee.objects.filter(pk__in=pk_set)
        for committee in committees:
            committee.group.user_set.add(instance.user)
    elif action == "pre_remove":
        committees = Committee.objects.filter(pk__in=pk_set)
        for committee in committees:
            committee.group.user_set.remove(instance.user)


class SystemAccess(models.Model):
    DRIVE = "drive"
    SLACK = "slack"
    CALENDAR = "calendar"
    TRELLO = "trello"
    EMAIL = "email"
    WEBSITE = "website"

    name_choices = (
        (DRIVE, _("Drive")),
        (SLACK, _("Slack")),
        (CALENDAR, _("Calendar")),
        (TRELLO, _("Trello")),
        (EMAIL, _("Email")),
        (WEBSITE, _("Website")),
    )

    name = models.fields.CharField(max_length=32, choices=name_choices, verbose_name=_("System"))
    value = models.fields.BooleanField(verbose_name=_("Access"))
    member = models.ForeignKey(Member, models.CASCADE, verbose_name="Member")

    @property
    def change_url(self):
        """
        The URL to change the system access. Depends on the type of system
        :return: An URL for the page where the access can be changed. Is an empty string if it should not be changed
        """
        if not self.should_be_changed():
            return ""

        # In the future it would be beneficial to create automated processes for adding, removing and revoking
        # access to the different systems automatically. E.g. a Slack App for adding/removing the user to the right
        # channels, or using GSuite APIs to add and remove people from mailing lists.
        return reverse("toggle-system-access", args=(self.pk,))

    def should_be_changed(self):
        return self.name != self.WEBSITE
