import itertools
from collections.abc import Collection
from datetime import datetime, time, timedelta
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.formats import time_format
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField

from news.models import TimePlace
from users.models import User
from util.locale_utils import exact_weekday_to_day_name, short_datetime_format, timedelta_to_hours
from util.model_utils import ComparisonType, comparison_boilerplate
from web.modelfields import UnlimitedCharField
from .machine import Machine, MachineType


class Quota(models.Model):
    all = models.BooleanField(default=False, verbose_name=_("all users"))
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quotas',
        verbose_name=_("user"),
    )
    machine_type = models.ForeignKey(
        to=MachineType,
        on_delete=models.CASCADE,
        related_name='quotas',
        verbose_name=_("machine type"),
    )
    number_of_reservations = models.IntegerField(default=1, verbose_name=_("number of reservations"))
    diminishing = models.BooleanField(default=False, verbose_name=_("diminishing"))
    ignore_rules = models.BooleanField(default=False, verbose_name=_("ignores rules"))

    class Meta:
        permissions = (
            ('can_create_event_reservation', "Can create event reservation"),
        )

    def __str__(self):
        if self.all:
            user_str = _("<all users>")
        else:
            user_str = self.user.get_full_name() if self.user else _("<nobody>")
        return _("Quota for {user} on {machine_type}").format(user=user_str, machine_type=self.machine_type)

    def get_unfinished_reservations(self, user: User):
        if self.diminishing:
            return self.reservations.all()
        reservations = self.reservations.filter(user=user) if self.all else self.reservations
        return reservations.filter(end_time__gte=timezone.now())

    def can_create_more_reservations(self, user: User):
        return self.number_of_reservations != self.get_unfinished_reservations(user).count()

    def is_valid_in(self, reservation: 'Reservation'):
        reservation_exists_or_can_make_more = (self.reservations.filter(pk=reservation.pk).exists()
                                               or self.can_create_more_reservations(reservation.user))
        ignore_rules_or_valid_time = (self.ignore_rules
                                      or ReservationRule.valid_time(reservation.start_time, reservation.end_time, reservation.machine.machine_type))
        return reservation_exists_or_can_make_more and ignore_rules_or_valid_time

    @classmethod
    def can_create_new_reservation(cls, user: User, machine_type: MachineType):
        return any(quota.can_create_more_reservations(user) for quota in cls.get_user_quotas(user, machine_type))

    @staticmethod
    def get_user_quotas(user: User, machine_type: MachineType):
        return machine_type.quotas.filter(Q(user=user) | Q(all=True))

    @classmethod
    def get_best_quota(cls, reservation: 'Reservation') -> Optional['Quota']:
        """
        Selects the best quota for the given reservation,
        by preferring non-diminishing quotas that do not ignore the rules.

        :param reservation: The reservation to check
        :return: The best quota, that can handle the given reservation, or None if none can
        """
        valid_quotas = [quota for quota in cls.get_user_quotas(reservation.user, reservation.machine.machine_type) if
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

    @classmethod
    def can_create_reservation(cls, reservation: 'Reservation'):
        return cls.get_best_quota(reservation) is not None


class Reservation(models.Model):
    # The amount of time into the future that regular users are allowed to create reservations
    # (applies to both `start_time` and `end_time`)
    FUTURE_LIMIT = timedelta(days=28)
    # It's allowed to set start/end times up to this amount of time in the past
    GRACE_PERIOD_FOR_SETTING_TIMES = timedelta(minutes=5)

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

    class Meta:
        permissions = (
            ('can_view_reservation_user', "Can view reservation user"),
        )

    def __str__(self):
        start_time = short_datetime_format(self.start_time)
        end_time = short_datetime_format(self.end_time)
        return f"{self.user.get_full_name()} har reservert {self.machine.name} fra {start_time} til {end_time}"

    def __bool__(self):
        # As long as the instance is not None, it should always return True.
        # (Implementing this method explicitly, due to the below implementation of `__len__()`
        # messing with Python's standard truth value testing.)
        return True

    def __len__(self) -> timedelta:
        return self.end_time - self.start_time

    def __sub__(self, other) -> timedelta:
        comparison_boilerplate(self, other, ComparisonType.SUB)

        return self.start_time - other.end_time

    def save(self, *args, **kwargs):
        if not self.validate():
            raise ValidationError("Not a valid reservation")

        # Do not connect the reservation to a quota if it is not a personal reservation
        if not (self.event or self.special):
            self.quota = Quota.get_best_quota(self)

        super().save(*args, **kwargs)

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

        earliest_allowed_time_to_set = self.get_earliest_allowed_time_to_set()
        # Check if the user can change the reservation
        if self.pk:
            old_reservation = Reservation.objects.get(pk=self.pk)
            can_change = self.can_change(self.user)
            can_change_end_time = old_reservation.can_change_end_time(self.user)
            valid_end_time_change = (old_reservation.start_time == self.start_time
                                     and self.end_time >= earliest_allowed_time_to_set)
            if not can_change and not (can_change_end_time and valid_end_time_change):
                return False

        if not self.pk and self.start_time < earliest_allowed_time_to_set:
            return False

        # Check if the user can make the given reservation/edit
        return self.quota_can_create_reservation()

    def starts_before_now(self):
        """Check if the start time is before current time."""
        return self.start_time < timezone.now()

    def check_start_time_after_end_time(self):
        """Check if start time is after end time."""
        return self.start_time >= self.end_time

    def quota_can_create_reservation(self):
        """Check if the user can make the given reservation/edit."""
        return Quota.can_create_reservation(self)

    def is_within_allowed_period(self):
        """Check if the reservation is made within the reservation_future_limit."""
        return self.end_time <= timezone.now() + self.FUTURE_LIMIT

    def check_machine_out_of_order(self):
        """Check if the machine is listed as out of order."""
        return self.machine.get_status() == Machine.Status.OUT_OF_ORDER

    def check_machine_maintenance(self):
        """Check if the machine is listed as maintenance."""
        return self.machine.get_status() == Machine.Status.MAINTENANCE

    @classmethod
    def get_earliest_allowed_time_to_set(cls) -> datetime:
        return timezone.now() - cls.GRACE_PERIOD_FOR_SETTING_TIMES

    def can_delete(self, user: User):
        if user.has_perm('make_queue.delete_reservation'):
            return True
        return self.user == user and self.start_time > timezone.now()

    def can_change(self, user: User):
        if (user.has_perm('make_queue.can_create_event_reservation')
                and (self.special or (self.event is not None))):
            return True
        if self.start_time < timezone.now():
            return False
        return self.user == user or user.is_superuser

    def can_change_end_time(self, user: User):
        return self.end_time > timezone.now() and (self.user == user or user.is_superuser)


class ReservationRule(models.Model):
    class Day(models.IntegerChoices):
        # Values match the ones returned by `datetime.isoweekday()`
        MONDAY = 1, _("Monday")
        TUESDAY = 2, _("Tuesday")
        WEDNESDAY = 3, _("Wednesday")
        THURSDAY = 4, _("Thursday")
        FRIDAY = 5, _("Friday")
        SATURDAY = 6, _("Saturday")
        SUNDAY = 7, _("Sunday")

    DAY_INDEX_TO_NAME = dict(Day.choices)

    machine_type = models.ForeignKey(
        to=MachineType,
        on_delete=models.CASCADE,
        related_name='reservation_rules',
        verbose_name=_("machine type"),
    )
    start_time = models.TimeField(verbose_name=_("start time"))
    end_time = models.TimeField(verbose_name=_("end time"))
    days_changed = models.IntegerField(verbose_name=_("days"), help_text=_("Number of times midnight is passed between start and end time."))
    start_days = MultiSelectField(choices=Day.choices, min_choices=1, verbose_name=_("start days for rule periods"))
    max_hours = models.FloatField(verbose_name=_("hours single period"))
    max_inside_border_crossed = models.FloatField(verbose_name=_("hours multi-period"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    def __str__(self):
        start_time = time_format(self.start_time)
        end_time = time_format(self.end_time)
        # TODO: translate this and Reservation.__str__()
        days_str = f"{self.days_changed} {'dag' if self.days_changed == 1 else 'dager'}"
        return f"Regel for {self.machine_type}: {start_time}-{end_time} på {self.start_days}; {days_str}"

    @property
    def time_periods(self) -> list['Period']:
        return self.Period.list_from_start_weekdays(self.get_start_day_indices(), self.start_time, self.end_time, self.days_changed)

    def get_exact_start_and_end_times_list(self, *, iso=True, wrap_using_modulo=False) -> list[tuple[float, float]]:
        mod_divisor = 8 if iso else 7

        def mod(exact_weekday: float) -> float:
            if not wrap_using_modulo:
                return exact_weekday
            return exact_weekday % mod_divisor

        return [
            (mod(p.exact_start_weekday), mod(p.exact_end_weekday))
            for p in self.Period.list_from_start_weekdays(self.get_start_day_indices(iso=iso), self.start_time, self.end_time, self.days_changed)
        ]

    def get_start_day_indices(self, *, iso=True):
        shift = 0 if iso else -1
        return [int(day_index_str) + shift for day_index_str in self.start_days]

    @classmethod
    def valid_time(cls, start_time: datetime, end_time: datetime, machine_type: MachineType) -> bool:
        """
        Checks if a reservation in the supplied period is allowed by the rules for the machine type.

        :param start_time: The start time of the reservation
        :param end_time: The end time of the reservation
        :param machine_type: The type of machine for the reservation
        :return: A boolean indicating if the reservation follows the rules
        """
        duration = timedelta_to_hours(end_time - start_time)
        # Normal reservations (i.e. that do not ignore rules) will not be longer than 1 week
        if duration > (7 * 24):
            return False

        rules = cls.covered_rules(start_time, end_time, machine_type)
        # Only allow reservations when covered by at least one rule
        if not rules:
            return False

        # If the reservation is longer than allowed for all covered rules, then it cannot be allowed
        if duration > max(rule.max_hours for rule in rules):
            return False
        # If the reservation is shorter than allowed inside each of the covered rules, then it is always allowed
        if duration <= min(rule.max_hours for rule in rules):
            return True

        # Check if the reservation adheres to the inter-rule maxima
        return all(rule.valid_time_in_rule(start_time, end_time, len(rules) > 1) for rule in rules)

    def valid_time_in_rule(self, start_time: datetime, end_time: datetime, border_cross: bool) -> bool:
        if border_cross:
            return self.hours_inside(start_time, end_time) <= self.max_inside_border_crossed
        return timedelta_to_hours(end_time - start_time) <= self.max_hours

    def hours_inside(self, start_time: datetime, end_time: datetime) -> float:
        return sum(period.hours_inside(start_time, end_time) for period in self.time_periods)

    @staticmethod
    def covered_rules(start_time: datetime, end_time: datetime, machine_type: MachineType):
        """
        Finds the rules for the given machine type that are covered by the indicated period.

        :param start_time: The start time of the period
        :param end_time: The end time of the period
        :param machine_type: The type of machine
        :return: The rules for the machine type that are covered by the period
        """
        # If the reservation is longer than a week, it covers all rules
        if timedelta_to_hours(end_time - start_time) > 7 * 24:
            return machine_type.reservation_rules.all()

        return [rule for rule in machine_type.reservation_rules.all()
                if rule.hours_inside(start_time, end_time)]

    @staticmethod
    def rule_set_has_gaps(machine_type: MachineType):
        rules = machine_type.reservation_rules.all()
        if not rules:
            return True
        time_periods = itertools.chain(*(rule.time_periods for rule in rules))
        time_periods = sorted(time_periods, key=lambda p: p.exact_start_weekday)
        for i, period in enumerate(time_periods):
            next_period = time_periods[(i + 1) % len(time_periods)]
            if next_period - period > 0:
                return True
        return False

    class Period:

        def __init__(self, start_weekday: int, start_time: time, end_time: time, days_changed: int):
            self.start_time = start_time
            self.end_time = end_time
            self.exact_start_weekday = start_weekday + self.to_exact_num_days(start_time)
            self.exact_end_weekday = start_weekday + days_changed + self.to_exact_num_days(end_time)

        def __repr__(self):
            return f"<{type(self).__name__}: {self}>"

        def __str__(self):
            start_day_name = capfirst(exact_weekday_to_day_name(self.exact_start_weekday))
            end_day_name = exact_weekday_to_day_name(self.exact_end_weekday)
            return f"{start_day_name} {time_format(self.start_time)} &ndash; {end_day_name} {time_format(self.end_time)}"

        def __bool__(self):
            # As long as the instance is not None, it should always return True.
            # (Implementing this method explicitly, due to the below implementation of `__len__()`
            # messing with Python's standard truth value testing.)
            return True

        def __len__(self) -> float:
            return self.exact_end_weekday - self.exact_start_weekday

        def __sub__(self, other) -> float:
            """Assumes that there is no overlap between the two periods."""
            comparison_boilerplate(self, other, ComparisonType.SUB)

            if self.exact_start_weekday >= other.exact_end_weekday:
                return self.exact_start_weekday - other.exact_end_weekday
            else:
                return self.exact_start_weekday + 7 - other.exact_end_weekday

        @classmethod
        def from_rule(cls, start_weekday: int, rule: 'ReservationRule'):
            return cls(start_weekday, rule.start_time, rule.end_time, rule.days_changed)

        @classmethod
        def list_from_start_weekdays(cls, start_weekdays: Collection[int], start_time: time, end_time: time, days_changed: int):
            return [cls(start_weekday, start_time, end_time, days_changed) for start_weekday in start_weekdays]

        def hours_inside(self, start_time: datetime, end_time: datetime) -> float:
            exact_start_weekday = start_time.isoweekday() + self.to_exact_num_days(start_time.time())
            exact_end_weekday = end_time.isoweekday() + self.to_exact_num_days(end_time.time())
            return self.hours_overlap(
                (self.exact_start_weekday, self.exact_end_weekday),
                (exact_start_weekday, exact_end_weekday)
            )

        @staticmethod
        def hours_overlap(exact_weekday_range1: tuple[float, float], exact_weekday_range2: tuple[float, float]) -> float:
            start_weekday_1, end_weekday_1 = exact_weekday_range1
            start_weekday_2, end_weekday_2 = exact_weekday_range2

            # TODO: give variables proper names, or rewrite algorithm
            a = (end_weekday_1 - start_weekday_1) % 7
            b = (start_weekday_2 - start_weekday_1) % 7
            c = (end_weekday_2 - start_weekday_1) % 7

            if b > c:
                return min(a, c) * 24
            return (min(a, c) - min(a, b)) * 24

        @staticmethod
        def to_exact_num_days(time_: time) -> float:
            return time_.hour / 24 + time_.minute / (24 * 60) + time_.second / (24 * 60 * 60)

        def overlap(self, other: 'ReservationRule.Period'):
            hours_overlap = self.hours_overlap(
                (self.exact_start_weekday, self.exact_end_weekday),
                (other.exact_start_weekday, other.exact_end_weekday)
            )
            return hours_overlap > 0
