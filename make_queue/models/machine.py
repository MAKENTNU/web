from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Tuple, Union

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import F, Prefetch
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from users.models import User
from util.validators import lowercase_slug_validator
from web.modelfields import URLTextField, UnlimitedCharField
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField
from .course import Printer3DCourse


class MachineTypeQuerySet(models.QuerySet):

    def prefetch_machines_and_default_order_by(self, *, machines_attr_name: str):
        """
        Returns a ``QuerySet`` where all the machine types' machines have been prefetched
        and can be accessed through the attribute with the same name as ``machines_attr_name``.
        """
        return self.order_by('priority').prefetch_related(
            Prefetch('machines', queryset=Machine.objects.default_order_by(), to_attr=machines_attr_name)
        )


class MachineType(models.Model):
    class UsageRequirement(models.TextChoices):
        IS_AUTHENTICATED = 'AUTH', _("Only has to be logged in")
        TAKEN_3D_PRINTER_COURSE = '3DPR', _("Taken the 3D printer course")
        TAKEN_ADVANCED_3D_PRINTER_COURSE = "A3DP", _("Taken the advanced 3D printer course")

    name = MultiLingualTextField(unique=True)
    cannot_use_text = MultiLingualTextField(blank=True)
    usage_requirement = models.CharField(
        choices=UsageRequirement.choices,
        max_length=4,
        default=UsageRequirement.IS_AUTHENTICATED,
        verbose_name=_("usage requirement"),
    )
    has_stream = models.BooleanField(default=False)
    priority = models.IntegerField(
        verbose_name=_("priority"),
        help_text=_("The machine types are sorted ascending by this value."),
    )

    objects = MachineTypeQuerySet.as_manager()

    class Meta:
        ordering = ('priority',)

    def __str__(self):
        return str(self.name)

    def can_user_use(self, user: User):
        if self.usage_requirement == self.UsageRequirement.IS_AUTHENTICATED:
            return user.is_authenticated
        elif self.usage_requirement == self.UsageRequirement.TAKEN_3D_PRINTER_COURSE:
            return self.can_use_3d_printer(user)
        elif self.usage_requirement == self.UsageRequirement.TAKEN_ADVANCED_3D_PRINTER_COURSE:
            return self.can_use_advanced_3d_printer(user)
        return False

    @staticmethod
    def can_use_3d_printer(user: Union[User, AnonymousUser]):
        if not user.is_authenticated:
            return False
        if hasattr(user, 'printer_3d_course'):
            return True
        if Printer3DCourse.objects.filter(username=user.username).exists():
            course_registration = Printer3DCourse.objects.get(username=user.username)
            course_registration.user = user
            course_registration.save()
            return True
        return user.has_perm('make_queue.add_reservation')  # this will typically only be the case for superusers

    @staticmethod
    def can_use_advanced_3d_printer(user: Union[User, AnonymousUser]):
        if not user.is_authenticated:
            return False
        if Printer3DCourse.objects.filter(user=user).exists():
            course_registration = Printer3DCourse.objects.get(user=user)
            return course_registration.advanced_course
        if Printer3DCourse.objects.filter(username=user.username).exists():
            course_registration = Printer3DCourse.objects.get(username=user.username)
            course_registration.user = user
            course_registration.save()
            return course_registration.advanced_course
        return False


class MachineQuerySet(models.QuerySet):

    def default_order_by(self):
        return self.order_by(
            'machine_type__priority',
            F('priority').asc(nulls_last=True),
            Lower('name'),
        )


class Machine(models.Model):
    class Status(models.TextChoices):
        RESERVED = 'R', _("Reserved")
        AVAILABLE = 'F', _("Available")
        IN_USE = 'I', _("In use")
        OUT_OF_ORDER = 'O', _("Out of order")
        MAINTENANCE = 'M', _("Maintenance")

    STATUS_CHOICES_DICT = dict(Status.choices)

    name = UnlimitedCharField(unique=True, verbose_name=_("name"))
    stream_name = models.CharField(
        blank=True,
        max_length=50,
        default="",
        validators=[lowercase_slug_validator],
        verbose_name=_("stream name"),
        help_text=_("Used for connecting to the machine's stream."),
    )
    machine_model = UnlimitedCharField(verbose_name=_("machine model"))
    machine_type = models.ForeignKey(
        to=MachineType,
        on_delete=models.PROTECT,
        related_name='machines',
        verbose_name=_("machine type"),
    )
    location = UnlimitedCharField(verbose_name=_("location"))
    location_url = URLTextField(verbose_name=_("location URL"))
    status = models.CharField(choices=Status.choices, max_length=2, default=Status.AVAILABLE, verbose_name=_("status"))
    priority = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("priority"),
        help_text=_("If specified, the machines are sorted ascending by this value."),
    )
    notes = models.TextField(blank=True, verbose_name=_("notes"), help_text=_("This is only for internal use and is not displayed anywhere."))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    objects = MachineQuerySet.as_manager()

    def __str__(self):
        return f"{self.name} - {self.machine_model}"

    def get_next_reservation(self):
        return self.reservations.filter(start_time__gt=timezone.now()).order_by('start_time').first()

    @abstractmethod
    def can_user_use(self, user):
        return self.machine_type.can_user_use(user)

    def reservations_in_period(self, start_time: datetime, end_time: datetime):
        return (self.reservations.filter(start_time__lte=start_time, end_time__gt=start_time)
                | self.reservations.filter(start_time__gte=start_time, end_time__lte=end_time)
                | self.reservations.filter(start_time__lt=end_time, start_time__gt=start_time, end_time__gte=end_time))

    def get_status(self):
        if self.status in (self.Status.OUT_OF_ORDER, self.Status.MAINTENANCE):
            return self.status

        if self.reservations_in_period(timezone.now(), timezone.now() + timedelta(seconds=1)):
            return self.Status.RESERVED
        else:
            return self.Status.AVAILABLE

    def _get_FIELD_display(self, field):
        if field.attname == 'status':
            return self.STATUS_CHOICES_DICT[self.get_status()]
        return super()._get_FIELD_display(field)

    def reservable_status_display_tuple(self) -> Tuple[bool, str]:
        return (
            self.get_status() in {self.Status.AVAILABLE, self.Status.RESERVED, self.Status.IN_USE},
            self.get_status_display(),
        )


class MachineUsageRule(models.Model):
    """
    Allows for specification of rules for each type of machine.
    """
    machine_type = models.OneToOneField(
        to=MachineType,
        on_delete=models.CASCADE,
        related_name='usage_rule',
    )
    content = MultiLingualRichTextUploadingField(verbose_name=_("content"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    history = HistoricalRecords(excluded_fields=['last_modified'])

    def __str__(self):
        return _("Usage rules for {machine_type}").format(machine_type=self.machine_type)
