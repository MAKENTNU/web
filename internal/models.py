from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import F
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers.phonenumberutil import region_code_for_number
from simple_history.models import HistoricalRecords

from groups.models import Committee
from users.models import User
from web.modelfields import UnlimitedCharField
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField
from .modelfields import SemesterField
from .util import date_to_semester, year_to_semester
from .validators import WhitelistedEmailValidator, discord_username_validator


class Member(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name='member',
        verbose_name=_("user"),
    )
    committees = models.ManyToManyField(
        to=Committee,
        blank=True,
        related_name='members',
        verbose_name=_("committees"),
    )
    role = UnlimitedCharField(blank=True, verbose_name=_("role"))
    contact_email = models.EmailField(blank=True, verbose_name=_("contact email"))
    gmail = models.EmailField(blank=True, verbose_name=_("Gmail"))
    MAKE_email = models.EmailField(blank=True, validators=[WhitelistedEmailValidator(valid_domains=["makentnu.no"])],
                                   verbose_name=_("MAKE email"))
    phone_number = PhoneNumberField(max_length=32, blank=True, verbose_name=_("phone number"))
    study_program = UnlimitedCharField(blank=True, verbose_name=_("study program"))
    ntnu_starting_semester = SemesterField(null=True, blank=True, verbose_name=_("starting semester at NTNU"),
                                           help_text=_('Must be in the format [V/H][year], e.g. “V17” or “H2017”.'))
    date_joined = models.DateField(default=timezone.datetime.now, verbose_name=_("date joined"))
    date_quit_or_retired = models.DateField(null=True, blank=True, verbose_name=_("date quit or retired"))
    reason_quit = models.TextField(blank=True, verbose_name=_("reason quit"))
    comment = models.TextField(blank=True, verbose_name=_("comment"))
    active = models.BooleanField(default=True, verbose_name=_("is active"))
    guidance_exemption = models.BooleanField(default=False, verbose_name=_("guidance exemption"))
    quit = models.BooleanField(default=False, verbose_name=_("has quit"))
    retired = models.BooleanField(default=False, verbose_name=_("retired"))
    honorary = models.BooleanField(default=False, verbose_name=_("honorary"))
    # Our code shouldn't have to keep track of these services' username length constraints, so we should not limit the length
    github_username = UnlimitedCharField(blank=True, verbose_name=_("GitHub username"))
    discord_username = UnlimitedCharField(blank=True, validators=[discord_username_validator], verbose_name=_("Discord username"))
    minecraft_username = UnlimitedCharField(blank=True, verbose_name=_("Minecraft username"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        permissions = (
            ('is_internal', "Is a member of MAKE NTNU"),
            ('can_edit_group_membership', "Can edit the groups a member is part of, including (de)activation"),
            # WARNING: granting a user this permission enables them to carry out a stored XSS attack;
            #          only give trusted users/groups this permission
            ('can_change_rich_text_source', "Can change rich text fields' HTML source code directly (including adding <script> tags)"),
        )

    def __str__(self):
        return self.user.get_full_name()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        is_creation = self.pk is None

        super().save(force_insert, force_update, using, update_fields)

        if is_creation:
            # Setup all properties for new members
            for property_name, value in SystemAccess.NAME_CHOICES:
                # All members will be registered on the website when added to the member list
                SystemAccess.objects.create(name=property_name, member=self,
                                            value=property_name == SystemAccess.WEBSITE)

            # Add user to the MAKE group
            self.set_membership(True)

    @property
    def phone_number_display(self):
        if not isinstance(self.phone_number, PhoneNumber):
            return self.phone_number

        if region_code_for_number(self.phone_number) == settings.PHONENUMBER_DEFAULT_REGION:
            return self.phone_number.as_national
        else:
            return self.phone_number.as_international

    @property
    def ntnu_starting_semester_display(self):
        if not self.ntnu_starting_semester:
            return ""
        return year_to_semester(self.ntnu_starting_semester)

    @property
    def semester_joined(self):
        return date_to_semester(self.date_joined)

    @property
    def semester_quit_or_retired(self):
        if self.date_quit_or_retired is None:
            return None
        return date_to_semester(self.date_quit_or_retired)

    def set_quit(self, quit_status: bool, reason="", date_quit_or_retired=timezone.now()):
        """
        Perform all the actions to set a member as quit or undo this action.

        :param quit_status: Indicates if the member has quit
        :param reason: The reason why the member has quit
        :param date_quit_or_retired: The date the member quit
        """
        self.quit = quit_status
        if self.quit:
            self.date_quit_or_retired = date_quit_or_retired
        else:
            self.date_quit_or_retired = None

        self.reason_quit = reason
        self.set_committee_membership(not quit_status)
        self.set_membership(not quit_status)

    def set_retirement(self, retirement_status: bool, date_quit_or_retired=timezone.now()):
        """
        Perform all the actions to set a member as retired or to undo this action.

        :param retirement_status: Indicates if the member has retired
        :param date_quit_or_retired: The date the member retired
        """
        self.retired = retirement_status
        if self.retired:
            self.date_quit_or_retired = date_quit_or_retired
        else:
            self.date_quit_or_retired = None

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
        # `capfirst()` to avoid duplicate translation differing only in case
        (EMAIL, capfirst(_("email"))),
        (WEBSITE, _("Website")),
    )

    member = models.ForeignKey(
        to=Member,
        on_delete=models.CASCADE,
        related_name='system_accesses',
        verbose_name=_("member"),
    )
    name = models.fields.CharField(choices=NAME_CHOICES, max_length=32, verbose_name=_("system"))
    value = models.fields.BooleanField(verbose_name=_("access"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('name', 'member'), name="%(class)s_unique_name_per_member"),
        )
        verbose_name = "system access"
        verbose_name_plural = "system accesses"

    def __str__(self):
        return _("Access for {member} to {name}: {has_access}").format(member=self.member, name=self.name, has_access=self.value)

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
        return reverse('edit_system_access', args=(self.member.pk, self.pk))

    def should_be_changed(self):
        return self.name != self.WEBSITE


class SecretQuerySet(models.QuerySet):

    def default_order_by(self):
        return self.order_by(
            F('priority').asc(nulls_last=True),
            Lower('title'),
        )


class Secret(models.Model):
    title = MultiLingualTextField(
        max_length=100,
        unique=True,
        verbose_name=_("title"),
    )
    content = MultiLingualRichTextUploadingField(verbose_name=_("description"))
    priority = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("priority"),
        help_text=_("If specified, the secrets are sorted ascending by this value."),
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    objects = SecretQuerySet.as_manager()

    history = HistoricalRecords(excluded_fields=['priority', 'last_modified'])

    def __str__(self):
        return str(self.title)


class Quote(models.Model):
    quote = models.TextField(verbose_name=_("quote"))
    quoted = models.CharField(max_length=100, verbose_name=_("quoted"), help_text=_("The person who is quoted."))
    context = models.TextField(blank=True, max_length=500, verbose_name=_("context"))
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='quotes',
        verbose_name=_("author"),
    )

    def __str__(self):
        return _("“{quote}” —{quoted}").format(quote=self.quote, quoted=self.quoted)
