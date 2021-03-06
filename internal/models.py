from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from groups.models import Committee
from users.models import User
from web.modelfields import UnlimitedCharField
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField
from .util import date_to_term


class Member(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.DO_NOTHING,
        null=True,
        verbose_name=_("User"),
    )
    committees = models.ManyToManyField(
        to=Committee,
        blank=True,
        verbose_name=_("Committees"),
    )
    role = UnlimitedCharField(blank=True, verbose_name=_("Role"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone_number = PhoneNumberField(max_length=32, blank=True, verbose_name=_("Phone number"))
    study_program = UnlimitedCharField(blank=True, verbose_name=_("Study program"))
    date_joined = models.DateField(default=timezone.datetime.now, verbose_name=_("Date joined"))
    date_quit = models.DateField(null=True, blank=True, verbose_name=_("Date quit"))
    reason_quit = models.TextField(blank=True, verbose_name=_("Reason quit"))
    comment = models.TextField(blank=True, verbose_name=_("Comment"))
    active = models.BooleanField(default=True, verbose_name=_("Is active"))
    guidance_exemption = models.BooleanField(default=False, verbose_name=_("Guidance exemption"))
    quit = models.BooleanField(default=False, verbose_name=_("Has quit"))
    retired = models.BooleanField(default=False, verbose_name=_("Retired"))
    honorary = models.BooleanField(default=False, verbose_name=_("Honorary"))

    class Meta:
        permissions = (
            ('is_internal', "Is a member of MAKE NTNU"),
            ('can_register_new_member', "Can register new member"),
            ('can_edit_group_membership', "Can edit the groups a member is part of, including (de)activation"),
        )

    def __str__(self):
        return self.user.get_full_name()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        is_creation = self.pk is None

        super().save(force_insert, force_update, using, update_fields)

        if is_creation:
            self.email = self.user.email

            # Setup all properties for new members
            for property_name, value in SystemAccess.NAME_CHOICES:
                # All members will be registered on the website when added to the members list
                SystemAccess.objects.create(name=property_name, member=self,
                                            value=property_name == SystemAccess.WEBSITE)

            # Add user to the MAKE group
            self.set_membership(True)

    @property
    def term_joined(self):
        return date_to_term(self.date_joined)

    @property
    def term_quit(self):
        if self.date_quit is None:
            return None
        return date_to_term(self.date_quit)

    def set_quit(self, quit_status: bool, reason="", date_quit=timezone.now()):
        """
        Perform all the actions to set a member as quit or undo this action.

        :param quit_status: Indicates if the member has quit
        :param reason: The reason why the member has quit
        :param date_quit: The date the member quit
        """
        self.quit = quit_status
        if self.quit:
            self.date_quit = date_quit
        else:
            self.date_quit = None

        self.reason_quit = reason
        self.set_committee_membership(not quit_status)
        self.set_membership(not quit_status)

    def set_retirement(self, retirement_status: bool):
        """
        Perform all the actions to set a member as retired or to undo this action.

        :param retirement_status: Indicates if the member has retired
        """
        self.retired = retirement_status
        self.set_committee_membership(not retirement_status)
        self.set_membership(True)

    def set_committee_membership(self, membership_status):
        """
        Add or remove the user from all the committees of their membership.

        :param membership_status: Indicates if the member should be a part of the commitees
        """
        for committee in self.committees.all():
            if membership_status:
                committee.group.user_set.add(self.user)
            else:
                committee.group.user_set.remove(self.user)

    def set_membership(self, membership_status):
        """
        Set membership by removing/adding the member to the MAKE group (if it exists).

        :param membership_status: True if the user should be a member of MAKE and false otherwise
        """
        make = Group.objects.filter(name="MAKE")
        if make.exists():
            if membership_status:
                make.first().user_set.add(self.user)
            else:
                make.first().user_set.remove(self.user)


@receiver(m2m_changed, sender=Member.committees.through)
def member_update_user_groups(sender, instance, action="", pk_set=None, **kwargs):
    """
    Makes sure that the member is added/removed from the correct groups as their committee membership changes.
    """
    if action == 'pre_add':
        committees = Committee.objects.filter(pk__in=pk_set)
        for committee in committees:
            committee.group.user_set.add(instance.user)
    elif action == 'pre_remove':
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

    NAME_CHOICES = (
        (DRIVE, _("Drive")),
        (SLACK, _("Slack")),
        (CALENDAR, _("Calendar")),
        (TRELLO, _("Trello")),
        (EMAIL, _("Email")),
        (WEBSITE, _("Website")),
    )

    member = models.ForeignKey(
        to=Member,
        on_delete=models.CASCADE,
        verbose_name=_("Member"),
    )
    name = models.fields.CharField(choices=NAME_CHOICES, max_length=32, verbose_name=_("System"))
    value = models.fields.BooleanField(verbose_name=_("Access"))

    @property
    def change_url(self):
        """
        The URL to change the system access. Depends on the type of system.

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


class Secret(models.Model):
    title = MultiLingualTextField(
        max_length=100,
        unique=True,
        verbose_name=_("Title"),
    )
    content = MultiLingualRichTextUploadingField(verbose_name=_("Description"))
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.title)
