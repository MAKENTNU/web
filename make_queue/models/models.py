from abc import abstractmethod
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from make_queue.fields import MachineTypeField
from make_queue.util.time import timedelta_to_hours
from news.models import TimePlace
from web.multilingual.database import MultiLingualRichTextUploadingField


class Machine(models.Model):
    status_choices = (
        ("R", _("Reserved")),
        ("F", _("Available")),
        ("I", _("In use")),
        ("O", _("Out of order")),
        ("M", _("Maintenance")),
    )

    status = models.CharField(max_length=2, choices=status_choices, verbose_name=_("Status"), default="F")
    name = models.CharField(max_length=30, unique=True, verbose_name=_("Name"))
    location = models.CharField(max_length=40, verbose_name=_("Location"))
    location_url = models.URLField(verbose_name=_("Location URL"))
    machine_model = models.CharField(max_length=40, verbose_name=_("Machine model"))
    machine_type = MachineTypeField(null=True, verbose_name=_("Machine type"))

    @abstractmethod
    def get_reservation_set(self):
        return Reservation.objects.filter(machine=self)

    def get_next_reservation(self):
        return self.get_reservation_set().filter(start_time__gt=timezone.now()).order_by('start_time').first()

    @abstractmethod
    def can_user_use(self, user):
        return self.machine_type.can_user_use(user)

    def reservations_in_period(self, start_time, end_time):
        return self.get_reservation_set().filter(start_time__lte=start_time, end_time__gt=start_time) | \
               self.get_reservation_set().filter(start_time__gte=start_time, end_time__lte=end_time) | \
               self.get_reservation_set().filter(start_time__lt=end_time, start_time__gt=start_time,
                                                 end_time__gte=end_time)

    def __str__(self):
        return self.name + " - " + self.machine_model

    def get_status(self):
        if self.status in "OM":
            return self.status
        return self.reservations_in_period(timezone.now(), timezone.now() + timedelta(seconds=1)) and "R" or "F"

    def _get_FIELD_display(self, field):
        if field.attname == "status":
            return self._get_status_display()
        return super()._get_FIELD_display(field)

    def _get_status_display(self):
        current_status = self.get_status()
        return [full_name for short_hand, full_name in self.status_choices if short_hand == current_status][0]


class MachineUsageRule(models.Model):
    """
    Allows for specification of rules for each type of machine
    """
    machine_type = MachineTypeField(unique=True)
    content = MultiLingualRichTextUploadingField()


class Quota(models.Model):
    number_of_reservations = models.IntegerField(default=1, verbose_name=_("Number of reservations"))
    diminishing = models.BooleanField(default=False, verbose_name=_("Diminishing"))
    ignore_rules = models.BooleanField(default=False, verbose_name=_("Ignores rules"))
    all = models.BooleanField(default=False, verbose_name=_("All users"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name=_("User"))
    machine_type = MachineTypeField(null=True, verbose_name=_("Machine type"))

    class Meta:
        permissions = (
            ("can_create_event_reservation", "Can create event reservation"),
            ("can_edit_quota", "Can edit quotas"),
        )

    def get_active_reservations(self, user):
        if self.diminishing:
            return self.reservation_set.all()
        reservation_set = self.reservation_set if not self.all else self.reservation_set.filter(user=user)
        return reservation_set.all().filter(end_time__gte=timezone.now())

    def can_make_more_reservations(self, user):
        return self.number_of_reservations != self.get_active_reservations(user).count()

    def is_valid_in(self, reservation):
        return (self.reservation_set.filter(pk=reservation.pk).exists() or
                self.can_make_more_reservations(reservation.user)) and \
               (self.ignore_rules or ReservationRule.valid_time(reservation.start_time, reservation.end_time,
                                                                reservation.machine.machine_type))

    @staticmethod
    def can_make_new_reservation(user, machine_type):
        return any(quota.can_make_more_reservations(user) for quota in Quota.get_user_quotas(user, machine_type))

    @staticmethod
    def get_user_quotas(user, machine_type):
        return Quota.objects.filter(Q(user=user) | Q(all=True)).filter(machine_type=machine_type)

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
    def can_make_reservation(reservation):
        return Quota.get_best_quota(reservation) is not None


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event = models.ForeignKey(TimePlace, null=True, blank=True, on_delete=models.CASCADE)
    showed = models.NullBooleanField(default=None)
    special = models.BooleanField(default=False)
    special_text = models.CharField(max_length=64)
    reservation_future_limit_days = 28
    comment = models.TextField(max_length=2000, default="")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    quota = models.ForeignKey(Quota, on_delete=models.CASCADE, null=True)

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
            return self.user.has_perm("make_queue.can_create_event_reservation")

        # Limit the amount of time forward in time a reservation can be made
        if not self.is_within_allowed_period_for_reservation():
            return False

        # Check if the user can change the reservation
        if self.pk:
            old_reservation = Reservation.objects.get(pk=self.pk)
            can_change = self.can_change(self.user)
            can_change_end_time = old_reservation.can_change_end_time(self.user)
            valid_end_time_change = old_reservation.start_time == self.start_time and \
                                    self.end_time >= timezone.now() - timedelta(minutes=5)
            if not can_change and not (can_change_end_time and valid_end_time_change):
                return False

        if not self.pk and self.start_time < timezone.now() - timedelta(minutes=5):
            return False

        # Check if the user can make the given reservation/edit
        return self.quota_can_make_reservation(self)

    # Check if the start time is before current time
    def reservation_starts_before_now(self):
        return self.start_time < timezone.now()

    # Check if start time is after end time
    def check_start_time_after_end_time(self):
        return self.start_time >= self.end_time

    # Check if reservation is within the quota
    def quota_can_make_reservation(self):
        return Quota.can_make_reservation(self)

    # Check if the reservation is made within the reservation_future_limit
    def is_within_allowed_period_for_reservation(self):
        return self.end_time <= timezone.now() + timedelta(days=self.reservation_future_limit_days)

    def can_delete(self, user):
        if user.has_perm("make_queue.delete_reservation"):
            return True
        return self.user == user and self.start_time > timezone.now()

    def can_change(self, user):
        if user.has_perm("make_queue.can_create_event_reservation") and (self.special or (self.event is not None)):
            return True
        if self.start_time < timezone.now():
            return False
        return self.user == user

    def can_change_end_time(self, user):
        return self.end_time > timezone.now() and self.user == user

    class Meta:
        permissions = (
            ("can_view_reservation_user", "Can view reservation user"),
        )

    def __str__(self):
        return "{:} har reservert {:} fra {:} til {:}".format(self.user.get_full_name(), self.machine.name,
                                                              self.start_time.strftime("%d/%m/%Y - %H:%M"),
                                                              self.end_time.strftime("%d/%m/%Y - %H:%M"))


class ReservationRule(models.Model):
    start_time = models.TimeField(verbose_name=_("Start time"))
    end_time = models.TimeField(verbose_name=_("End time"))
    # Number of times passed by midnight between start and end time
    days_changed = models.IntegerField(verbose_name=_("Days"))
    start_days = models.IntegerField(default=0, verbose_name=_("Start days"))
    max_hours = models.FloatField(verbose_name=_("Hours single period"))
    max_inside_border_crossed = models.FloatField(verbose_name=_("Hours multiperiod"))
    machine_type = MachineTypeField(verbose_name=_("Machine type"))

    def save(self, **kwargs):
        if not self.is_valid_rule():
            raise ValidationError("Rule is not valid")
        return super().save(**kwargs)

    @staticmethod
    def valid_time(start_time, end_time, machine_type):
        # Normal non rule ignoring reservations will not be longer than 1 week
        if timedelta_to_hours(end_time - start_time) > 168:
            return False
        rules = [rule for rule in ReservationRule.objects.filter(machine_type=machine_type) if
                 rule.hours_inside(start_time, end_time)]
        if timedelta_to_hours(end_time - start_time) > max(rule.max_hours for rule in rules):
            return False

        if timedelta_to_hours(end_time - start_time) <= min(rule.max_hours for rule in rules):
            return True

        return all(rule.valid_time_in_rule(start_time, end_time, len(rules) > 1) for rule in rules)

    class Period:
        def __init__(self, start_day, rule):
            self.start_time = self.__to_inner_rep(start_day, rule.start_time)
            self.end_time = self.__to_inner_rep(start_day + rule.days_changed, rule.end_time)
            self.rule = rule

        def hours_inside(self, start_time, end_time):
            return self.hours_overlap(self.start_time, self.end_time,
                                      self.__to_inner_rep(start_time.weekday(), start_time.time()),
                                      self.__to_inner_rep(end_time.weekday(), end_time.time()))

        @staticmethod
        def hours_overlap(a, b, c, d):
            b, c, d = (b - a) % 7, (c - a) % 7, (d - a) % 7

            if c > d:
                return min(b, d) * 24
            return (min(b, d) - min(b, c)) * 24

        @staticmethod
        def __to_inner_rep(day, time):
            return day + time.hour / 24 + time.minute / 1440 + time.second / 86400

        def overlap(self, other):
            return self.hours_overlap(self.start_time, self.end_time, other.start_time, other.end_time) > 0

    def is_valid_rule(self, raise_error=False):
        # Check if the time period is a valid time period (within a week)
        if self.start_time > self.end_time and not self.days_changed or self.days_changed > 7 or \
                self.days_changed == 7 and self.start_time < self.end_time:
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
                              ReservationRule.objects.filter(machine_type=self.machine_type).exclude(pk=self.pk) for
                              time_period in rule.time_periods()]

        other_overlap = any(t1.overlap(t2) for t1 in time_periods for t2 in other_time_periods)

        if raise_error and other_overlap:
            raise ValidationError("Rule time periods overlap with time periods of other rules.")

        return not other_overlap

    def valid_time_in_rule(self, start_time, end_time, border_cross):
        if border_cross:
            return self.hours_inside(start_time, end_time) <= self.max_inside_border_crossed
        return timedelta_to_hours(end_time - start_time) <= self.max_hours

    def hours_inside(self, start_time, end_time):
        return sum(period.hours_inside(start_time, end_time) for period in self.time_periods())

    def time_periods(self):
        return [self.Period(day_index, self) for day_index, _ in
                filter(lambda enumerate_obj: enumerate_obj[1] == "1", enumerate(format(self.start_days, "07b")[::-1]))]
