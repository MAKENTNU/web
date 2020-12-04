from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Union

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import F, Prefetch
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.models import User
from web.modelfields import URLTextField, UnlimitedCharField
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField
from .course import Printer3DCourse


class MachineTypeQuerySet(models.QuerySet):

    def prefetch_machines_and_default_order_by(self, *, machines_attr_name: str):
        """
        Returns a ``QuerySet`` where all the ``MachineType``'s machines have been prefetched
        and can be accessed through the attribute with the same name as ``machines_attr_name``.
        """
        return self.order_by('priority').prefetch_related(
            Prefetch('machines', queryset=Machine.objects.default_order_by(), to_attr=machines_attr_name)
        )


class MachineType(models.Model):
    class UsageRequirement(models.TextChoices):
        IS_AUTHENTICATED = 'AUTH', _("Only has to be logged in")
        TAKEN_3D_PRINTER_COURSE = '3DPR', _("Taken the 3D printer course")

    name = MultiLingualTextField(unique=True)
    cannot_use_text = MultiLingualTextField(blank=True)
    usage_requirement = models.CharField(
        choices=UsageRequirement.choices,
        max_length=4,
        default=UsageRequirement.IS_AUTHENTICATED,
        verbose_name=_("Usage requirement"),
    )
    has_stream = models.BooleanField(default=False)
    priority = models.IntegerField(
        verbose_name=_("Priority"),
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
        return False

    @staticmethod
    def can_use_3d_printer(user: Union[User, AnonymousUser]):
        if not user.is_authenticated:
            return False
        if hasattr(user, 'printer_3d_course'):
            return True
        # TODO: remove
        if Printer3DCourse.objects.filter(username=user.username).exists():
            course_registration = Printer3DCourse.objects.get(username=user.username)
            course_registration.user = user
            course_registration.save()
            return True
        return user.has_perm('make_queue.add_reservation')  # this will typically only be the case for superusers


class MachineQuerySet(models.QuerySet):

    def default_order_by(self):
        return self.order_by(
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

    name = UnlimitedCharField(unique=True, verbose_name=_("Name"))
    machine_model = UnlimitedCharField(verbose_name=_("Machine model"))
    machine_type = models.ForeignKey(
        to=MachineType,
        on_delete=models.PROTECT,
        related_name='machines',
        verbose_name=_("Machine type"),
    )
    location = UnlimitedCharField(verbose_name=_("Location"))
    location_url = URLTextField(verbose_name=_("Location URL"))
    # TODO: add static image to Machine
    # static_image = models.ImageField(upload_to='machines', verbose_name=_("Static image"))
    status = models.CharField(choices=Status.choices, max_length=2, default=Status.AVAILABLE, verbose_name=_("Status"))
    priority = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Priority"),
        help_text=_("If specified, the machines are sorted ascending by this value."),
    )

    objects = MachineQuerySet.as_manager()

    def get_next_reservation(self):
        return self.reservations.filter(start_time__gt=timezone.now()).order_by('start_time').first()

    @abstractmethod
    def can_user_use(self, user):
        return self.machine_type.can_user_use(user)

    def reservations_in_period(self, start_time: datetime, end_time: datetime):
        return (self.reservations.filter(start_time__lte=start_time, end_time__gt=start_time)
                | self.reservations.filter(start_time__gte=start_time, end_time__lte=end_time)
                | self.reservations.filter(start_time__lt=end_time, start_time__gt=start_time, end_time__gte=end_time))

    def __str__(self):
        return f"{self.name} - {self.machine_model}"

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

    @property
    def is_reservable(self):
        return self.get_status() in {self.Status.AVAILABLE, self.Status.RESERVED, self.Status.IN_USE}


class MachineUsageRule(models.Model):
    """
    Allows for specification of rules for each type of machine
    """
    machine_type = models.OneToOneField(
        to=MachineType,
        on_delete=models.CASCADE,
        related_name='usage_rule',
    )
    content = MultiLingualRichTextUploadingField()

    def __str__(self):
        return _("Usage rules for {machine_type}").format(machine_type=self.machine_type)
