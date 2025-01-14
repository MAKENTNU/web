from abc import abstractmethod
from datetime import datetime, timedelta

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import F, Prefetch, Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse
from simple_history.models import HistoricalRecords

from users.models import User
from util.validators import lowercase_slug_validator
from web.modelfields import URLTextField, UnlimitedCharField
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField
from .course import CoursePermission, Printer3DCourse


class MachineTypeQuerySet(models.QuerySet):

    def default_order_by(self) -> 'MachineTypeQuerySet[MachineType]':
        return self.order_by('priority')

    def prefetch_machines(self, *, machine_queryset=None, machines_attr_name: str) -> 'MachineTypeQuerySet[MachineType]':
        """
        Returns a ``QuerySet`` where all the machine types' machines have been prefetched
        and can be accessed through the attribute with the same name as ``machines_attr_name``.
        """
        if machine_queryset is None:
            machine_queryset = Machine.objects.all()
        return self.prefetch_related(
            Prefetch('machines', queryset=machine_queryset, to_attr=machines_attr_name)
        )


class MachineType(models.Model):

    name = MultiLingualTextField(unique=True)
    cannot_use_text = MultiLingualTextField(blank=True)
    usage_requirement = models.ForeignKey(CoursePermission, blank=True, null=True, verbose_name=_("usage requirement"), on_delete=models.PROTECT)
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
        if self.usage_requirement.short_name == "AUTH":
            return user.is_authenticated
        if self.usage_requirement.short_name == "3DPR":
            return self.can_use_3d_printer(user)
        return self.can_use_special_printer(user, self.usage_requirement)
    
    @staticmethod
    def can_use_3d_printer(user: User | AnonymousUser):
        if not user.is_authenticated:
            return False
        if hasattr(user, 'printer_3d_course'):
            return True
        if Printer3DCourse.objects.filter(username=user.username).exists():
            course_registration = Printer3DCourse.objects.get(username=user.username)
            course_registration.user = user
            course_registration.save()
            return True
        return user.has_perm('make_queue.add_reservation')  # This will typically only be the case for superusers
    
    @staticmethod
    def can_use_special_printer(user: User | AnonymousUser, permission: CoursePermission):
        if not user.is_authenticated:
            return False
        if Printer3DCourse.objects.filter(user=user).exists():
            course_registration = Printer3DCourse.objects.get(user=user)
            return permission in course_registration.course_permissions.all()
        if Printer3DCourse.objects.filter(username=user.username).exists():
            course_registration = Printer3DCourse.objects.get(username=user.username)
            course_registration.user = user
            course_registration.save()
            return permission in course_registration.course_permissions.all()
        return  False
    
class MachineQuerySet(models.QuerySet):

    def visible_to(self, user: User) -> 'MachineQuerySet[Machine]':
        if user.has_perm('internal.is_internal'):
            return self.all()

        exclude_query = Q(internal=True)
        # Machines that require the SLA course should not be visible to non-internal users who have not taken the SLA course
        if not hasattr(user, 'printer_3d_course') or not user.printer_3d_course.course_permissions.filter(short_name='SLAP').exists():
            exclude_query |= Q(machine_type__usage_requirement=CoursePermission.objects.get(short_name='SLAP'))
        return self.exclude(exclude_query)

    def default_order_by(self) -> 'MachineQuerySet[Machine]':
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
    internal = models.BooleanField(default=False, verbose_name=_("internal"),
                                   help_text=_("If selected, the machine will only be visible to and reservable by MAKE members."))
    status = models.CharField(choices=Status.choices, max_length=2, default=Status.AVAILABLE, verbose_name=_("status"))
    info_message = models.TextField(blank=True, verbose_name=_("info message"), help_text=_(
        "Information that's useful to know before using the machine, e.g. the filament that the 3D printer uses,"
        " the needle that's currently inserted in the sewing machine, or just the machine's current state/“mood” (emojis are allowed 🤠)."
    ))
    info_message_date = models.DateTimeField(blank=True, default=timezone.localtime, verbose_name=_("time the info message was changed"))
    priority = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("priority"),
        help_text=_("If specified, the machines are sorted ascending by this value."),
    )
    notes = models.TextField(blank=True, verbose_name=_("notes"), help_text=_("This is only for internal use and is not displayed anywhere."))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    objects = MachineQuerySet.as_manager()
    history = HistoricalRecords(excluded_fields=['status', 'info_message_date', 'priority', 'last_modified'])

    def __str__(self):
        return f"{self.name} - {self.machine_model}"

    def get_absolute_url(self):
        return reverse('machine_detail', args=[self.pk])

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

    def reservable_status_display_tuple(self) -> tuple[bool, str]:
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

    def get_absolute_url(self):
        return reverse('machine_usage_rule_detail', args=[self.machine_type.pk])
