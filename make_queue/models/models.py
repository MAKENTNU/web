from abc import abstractmethod
from datetime import datetime, timedelta
from typing import List, Union

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Prefetch, Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from make_queue.util.time import timedelta_to_hours
from news.models import TimePlace
from users.models import User
from web.fields import URLTextField, UnlimitedCharField
from web.multilingual.database import MultiLingualRichTextUploadingField, MultiLingualTextField
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
        if Printer3DCourse.objects.filter(user=user).exists():
            return True
        if Printer3DCourse.objects.filter(username=user.username).exists():
            course_registration = Printer3DCourse.objects.get(username=user.username)
            course_registration.user = user
            course_registration.save()
            return True
        return False


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


class Quota(models.Model):
    all = models.BooleanField(default=False, verbose_name=_("All users"))
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quotas',
        verbose_name=_("User"),
    )
    machine_type = models.ForeignKey(
        to=MachineType,
        on_delete=models.CASCADE,
        related_name='quotas',
        verbose_name=_("Machine type"),
    )
    number_of_reservations = models.IntegerField(default=1, verbose_name=_("Number of reservations"))
    diminishing = models.BooleanField(default=False, verbose_name=_("Diminishing"))
    ignore_rules = models.BooleanField(default=False, verbose_name=_("Ignores rules"))

    class Meta:
        permissions = (
            ('can_create_event_reservation', "Can create event reservation"),
            ('can_edit_quota', "Can edit quotas"),
        )

    def get_active_reservations(self, user):
        if self.diminishing:
            return self.reservations.all()
        reservations = self.reservations.filter(user=user) if self.all else self.reservations
        return reservations.filter(end_time__gte=timezone.now())

    def can_create_more_reservations(self, user):
        return self.number_of_reservations != self.get_active_reservations(user).count()

    def is_valid_in(self, reservation):
        reservation_exists_or_can_make_more = (self.reservations.filter(pk=reservation.pk).exists()
                                               or self.can_create_more_reservations(reservation.user))
        ignore_rules_or_valid_time = (self.ignore_rules
                                      or ReservationRule.valid_time(reservation.start_time, reservation.end_time, reservation.machine.machine_type))
        return reservation_exists_or_can_make_more and ignore_rules_or_valid_time

    @staticmethod
    def can_make_new_reservation(user, machine_type):
        return any(quota.can_create_more_reservations(user) for quota in Quota.get_user_quotas(user, machine_type))

    @staticmethod
    def get_user_quotas(user: User, machine_type: MachineType):
        return machine_type.quotas.filter(Q(user=user) | Q(all=True))

    @staticmethod
    def get_best_quota(reservation):
        """
        Selects the best quota for the given reservation, by preferring non-diminishing quotas that do not ignore the
        rules
        :param reservation: The reservation to check
        :return: The best quota, that can handle the given reservation, or None if none can
        """
        valid_quotas = [quota for quota in Quota.get_user_quotas(reservation.user, reservation.machine.machine_type) if
                        quota.is_valid_in(reservation)]

        if not valid_quotas:
            return None

        best_quota = valid_quotas[0]
        for quota in valid_quotas[1:]:
            if best_quota.diminishing:
                if not quota.diminishing or best_quota.ignore_rules and not quota.ignore_rules:
                    best_quota = quota
            elif best_quota.ignore_rules and not quota.ignore_rules:
                best_quota = quota

        return best_quota

    @staticmethod
    def can_create_reservation(reservation):
        return Quota.get_best_quota(reservation) is not None


class Reservation(models.Model):
    RESERVATION_FUTURE_LIMIT_DAYS = 28

    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    machine = models.ForeignKey(
        to=Machine,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event = models.ForeignKey(
        to=TimePlace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='machine_reservations',
    )
    special = models.BooleanField(default=False)
    special_text = UnlimitedCharField(blank=True)
    comment = models.TextField(blank=True)
    quota = models.ForeignKey(
        to=Quota,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reservations',
    )

    def save(self, *args, **kwargs):
        if not self.validate():
            raise ValidationError("Not a valid reservation")

        # Do not connect the reservation to a quota if it is not a personal reservation
        if not (self.event or self.special):
            self.quota = Quota.get_best_quota(self)

        super(Reservation, self).save(*args, **kwargs)

    # A reservation should not be able to be moved, only extended
    def validate(self):
        # User needs to be able to print, for it to be able to reserve the printers
        if not self.machine.can_user_use(self.user):
            return False

        # Check if the printer is already reserved by another reservation for the given duration
        if self.machine.reservations_in_period(self.start_time, self.end_time).exclude(pk=self.pk).exists():
            return False

        # A reservation must have a valid time period
        if self.check_start_time_after_end_time():
            return False

        # Event reservations are always valid, if the time is not already reserved
        if self.event or self.special:
            return self.user.has_perm('make_queue.can_create_event_reservation')

        # Limit the amount of time forward in time a reservation can be made
        if not self.is_within_allowed_period():
            return False

        # Check if machine is listed as out of order or maintenance
        if self.check_machine_out_of_order() or self.check_machine_maintenance():
            return False

        # Check if the user can change the reservation
        if self.pk:
            old_reservation = Reservation.objects.get(pk=self.pk)
            can_change = self.can_change(self.user)
            can_change_end_time = old_reservation.can_change_end_time(self.user)
            valid_end_time_change = (old_reservation.start_time == self.start_time
                                     and self.end_time >= timezone.now() - timedelta(minutes=5))
            if not can_change and not (can_change_end_time and valid_end_time_change):
                return False

        if not self.pk and self.start_time < timezone.now() - timedelta(minutes=5):
            return False

        # Check if the user can make the given reservation/edit
        return self.quota_can_create_reservation()

    def starts_before_now(self):
        """Check if the start time is before current time"""
        return self.start_time < timezone.now()

    def check_start_time_after_end_time(self):
        """Check if start time is after end time"""
        return self.start_time >= self.end_time

    def quota_can_create_reservation(self):
        """Check if the user can make the given reservation/edit"""
        return Quota.can_create_reservation(self)

    def is_within_allowed_period(self):
        """Check if the reservation is made within the reservation_future_limit"""
        return self.end_time <= timezone.now() + timedelta(days=self.RESERVATION_FUTURE_LIMIT_DAYS)

    def check_machine_out_of_order(self):
        """Check if the machine is listed as out of order"""
        return self.machine.get_status() == Machine.Status.OUT_OF_ORDER

    def check_machine_maintenance(self):
        """Check if the machine is listed as maintenance"""
        return self.machine.get_status() == Machine.Status.MAINTENANCE

    def can_delete(self, user):
        if user.has_perm('make_queue.delete_reservation'):
            return True
        return self.user == user and self.start_time > timezone.now()

    def can_change(self, user):
        if (user.has_perm('make_queue.can_create_event_reservation')
                and (self.special or (self.event is not None))):
            return True
        if self.start_time < timezone.now():
            return False
        return self.user == user

    def can_change_end_time(self, user):
        return self.end_time > timezone.now() and self.user == user

    class Meta:
        permissions = (
            ('can_view_reservation_user', "Can view reservation user"),
        )

    def __str__(self):
        start_time = self.start_time.strftime("%d/%m/%Y - %H:%M")
        end_time = self.end_time.strftime("%d/%m/%Y - %H:%M")
        return f"{self.user.get_full_name()} har reservert {self.machine.name} fra {start_time} til {end_time}"


class ReservationRule(models.Model):
    machine_type = models.ForeignKey(
        to=MachineType,
        on_delete=models.CASCADE,
        related_name='reservation_rules',
        verbose_name=_("Machine type"),
    )
    start_time = models.TimeField(verbose_name=_("Start time"))
    end_time = models.TimeField(verbose_name=_("End time"))
    # Number of times passed by midnight between start and end time
    days_changed = models.IntegerField(verbose_name=_("Days"))
    start_days = models.IntegerField(default=0, verbose_name=_("Start days"))
    max_hours = models.FloatField(verbose_name=_("Hours single period"))
    max_inside_border_crossed = models.FloatField(verbose_name=_("Hours multiperiod"))

    def save(self, **kwargs):
        if not self.is_valid_rule():
            raise ValidationError("Rule is not valid")
        return super().save(**kwargs)

    @staticmethod
    def valid_time(start_time: datetime, end_time: datetime, machine_type: MachineType) -> bool:
        duration = end_time - start_time
        # Normal non rule ignoring reservations will not be longer than 1 week
        if timedelta_to_hours(duration) > (7 * 24):
            return False
        rules = [rule for rule in machine_type.reservation_rules.all() if
                 rule.hours_inside(start_time, end_time)]
        if timedelta_to_hours(duration) > max(rule.max_hours for rule in rules):
            return False

        if timedelta_to_hours(duration) <= min(rule.max_hours for rule in rules):
            return True

        return all(rule.valid_time_in_rule(start_time, end_time, len(rules) > 1) for rule in rules)

    class Period:

        def __init__(self, start_weekday: int, rule: 'ReservationRule'):
            self.start_time = self.__to_inner_rep(start_weekday, rule.start_time)
            self.end_time = self.__to_inner_rep(start_weekday + rule.days_changed, rule.end_time)
            self.rule = rule

        def hours_inside(self, start_time: datetime, end_time: datetime) -> float:
            return self.hours_overlap(
                self.start_time, self.end_time,
                self.__to_inner_rep(start_time.weekday(), start_time.time()),
                self.__to_inner_rep(end_time.weekday(), end_time.time())
            )

        @staticmethod
        def hours_overlap(a, b, c, d):
            b, c, d = (b - a) % 7, (c - a) % 7, (d - a) % 7

            if c > d:
                return min(b, d) * 24
            return (min(b, d) - min(b, c)) * 24

        @staticmethod
        def __to_inner_rep(day, time):
            return day + time.hour / 24 + time.minute / (24 * 60) + time.second / (24 * 60 * 60)

        def overlap(self, other):
            return self.hours_overlap(
                self.start_time, self.end_time,
                other.start_time, other.end_time
            ) > 0

    def is_valid_rule(self, raise_error=False) -> bool:
        # Check if the time period is a valid time period (within a week)
        if (self.start_time > self.end_time and not self.days_changed
                or self.days_changed > 7
                or self.days_changed == 7 and self.start_time < self.end_time):
            if raise_error:
                raise ValidationError("Period is either too long (7+ days) or start time is earlier than end time.")
            return False

        # Check for internal overlap
        time_periods = self.time_periods()
        if any(t1.overlap(t2) for t1 in time_periods for t2 in time_periods if
               t1.end_time != t2.end_time and t1.start_time != t2.end_time):
            if raise_error:
                raise ValidationError("Rule has internal overlap of time periods.")
            return False

        # Check for overlap with other time periods
        other_time_periods = [time_period for rule in
                              self.machine_type.reservation_rules.exclude(pk=self.pk) for
                              time_period in rule.time_periods()]

        other_overlap = any(t1.overlap(t2) for t1 in time_periods for t2 in other_time_periods)

        if raise_error and other_overlap:
            raise ValidationError("Rule time periods overlap with time periods of other rules.")

        return not other_overlap

    def valid_time_in_rule(self, start_time: datetime, end_time: datetime, border_cross: bool) -> bool:
        if border_cross:
            return self.hours_inside(start_time, end_time) <= self.max_inside_border_crossed
        return timedelta_to_hours(end_time - start_time) <= self.max_hours

    def hours_inside(self, start_time: datetime, end_time: datetime) -> float:
        return sum(period.hours_inside(start_time, end_time) for period in self.time_periods())

    def time_periods(self) -> List[Period]:
        return [self.Period(day_index, self) for day_index, _ in
                filter(lambda enumerate_obj: enumerate_obj[1] == "1", enumerate(format(self.start_days, "07b")[::-1]))]
