from math import ceil

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from abc import abstractmethod, ABCMeta
from news.models import TimePlace


class Machine(models.Model):
    __metaclass__ = ABCMeta

    status_choices = (
        ("R", "Reservert"),
        ("F", "Ledig"),
        ("I", "I bruk"),
        ("O", "I ustand"),
        ("M", "Vedlikehold"),
    )

    status = models.CharField(max_length=2, choices=status_choices)
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=40)
    location_url = models.URLField()
    stream_url = models.URLField(default='')
    model = models.CharField(max_length=40)

    @abstractmethod
    def get_reservation_set(self):
        raise NotImplementedError

    @abstractmethod
    def can_user_use(self, user):
        """Abstract method"""

    def reservations_in_period(self, start_time, end_time):
        return self.get_reservation_set().filter(start_time__lte=start_time, end_time__gt=start_time) | \
               self.get_reservation_set().filter(start_time__gte=start_time, end_time__lte=end_time) | \
               self.get_reservation_set().filter(start_time__lt=end_time, start_time__gt=start_time,
                                                 end_time__gte=end_time)

    @staticmethod
    def get_subclass(machine_literal):
        return next(filter(lambda subclass: subclass.literal == machine_literal, Machine.__subclasses__()))

    def __str__(self):
        return self.name + " - " + self.model

    def get_status(self):
        if self.status in "OM":
            return self.status
        return self.reservations_in_period(timezone.now(), timezone.now() + timedelta(seconds=1)) and "R" or "F"

    def get_status_display(self):
        current_status = self.get_status()
        return [full_name for short_hand, full_name in self.status_choices if short_hand == current_status][0]


class Printer3D(Machine):
    literal = "3D-printer"
    cannot_use_text = "Reservasjon av 3D-printere krever fullført 3D-printer kurs. Hvis du har hatt kurset, men ikke " \
                      "har tilgang, ta kontakt med 3dprint@makentnu.no "

    def can_user_use(self, user):
        return hasattr(user, "quota3d") and user.quota3d.can_print

    def get_reservation_set(self):
        return self.reservation3d_set


class SewingMachine(Machine):
    literal = "Symaskin"

    def can_user_use(self, user):
        return True

    def get_reservation_set(self):
        return self.reservationsewing_set


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event = models.ForeignKey(TimePlace, null=True, blank=True, on_delete=models.CASCADE)
    showed = models.NullBooleanField(default=None)
    special = models.BooleanField(default=False)
    special_text = models.CharField(max_length=20)
    reservation_future_limit_days = 28
    comment = models.TextField(max_length=2000, default="")

    @abstractmethod
    def get_quota(self):
        raise NotImplementedError

    @abstractmethod
    def get_machine(self):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if not self.validate():
            raise ValidationError("Not a valid reservation")
        super(Reservation, self).save(*args, **kwargs)

    # A reservation should not be able to be moved, only extended
    def validate(self):
        # User needs to be able to print, for it to be able to reserve the printers
        if not self.get_machine().can_user_use(self.user):
            return False

        # Check if the printer is already reserved by another reservation for the given duration
        if self.get_machine().reservations_in_period(self.start_time, self.end_time).exclude(pk=self.pk).exists():
            return False

        # A reservation must have a valid time period
        if self.start_time >= self.end_time:
            return False

        # Event reservations are always valid, if the time is not already reserved
        if self.event or self.special:
            return self.user.has_perm("make_queue.can_create_event_reservation")

        # Limit the amount of time forward in time a reservation can be made
        if not self.is_within_allowed_period_for_reservation():
            return False

        # Check if the reservation is shorter than the maximum duration allowed for the user
        if self.end_time - self.start_time > timedelta(hours=self.get_quota().max_time_reservation):
            return False

        # Check if user has more than x% of reservations
        if self.has_reached_maximum_number_of_reservations():
            return False

        # If a primary key is set, the reservation is already saved once, and does not
        return self.pk is not None or self.get_quota().can_make_new_reservation()

    def is_within_allowed_period_for_reservation(self):
        return self.end_time <= timezone.now() + timedelta(days=self.reservation_future_limit_days)

    def has_reached_maximum_number_of_reservations(self):
        num_reservations_in_period = 0
        for machine in self.get_machine().__class__.objects.all():
            num_reservations_in_period += machine.reservations_in_period(self.start_time,
                                                                         self.end_time).filter(user=self.user,
                                                                                               event=None).exists()
        return (num_reservations_in_period + (self.pk is None)) > ceil(
            self.get_machine().__class__.objects.all().count() * self.percentage_of_machines_at_the_same_time)

    def can_delete(self):
        return self.start_time > timezone.now()

    def can_change(self, user):
        if self.start_time < timezone.now():
            return False
        if user.has_perm("make_queue.can_create_event_reservation") and (self.special or (self.event is not None)):
            return True
        return self.user == user

    class Meta:
        abstract = True
        permissions = (
            ("can_view_reservation_user", "Can view reservation user"),
        )

    @classmethod
    def get_reservation(cls, machine_type, pk):
        return cls.get_reservation_type(machine_type).objects.filter(pk=pk).first()

    @classmethod
    def get_reservation_type(cls, machine_type):
        return next(filter(lambda res: res.machine.field.target_field.model.literal == machine_type,
                           Reservation.__subclasses__()))


class Reservation3D(Reservation):
    machine = models.ForeignKey(Printer3D, on_delete=models.CASCADE)
    percentage_of_machines_at_the_same_time = 0.5

    def get_machine(self):
        return self.machine

    def get_quota(self):
        return Quota3D.get_quota(self.user)


class ReservationSewing(Reservation):
    machine = models.ForeignKey(SewingMachine, on_delete=models.CASCADE)
    percentage_of_machines_at_the_same_time = 1

    def get_machine(self):
        return self.machine

    def get_quota(self):
        return QuotaSewing.get_quota(self.user)


class Quota(models.Model):
    max_time_reservation = models.FloatField(default=16)
    max_number_of_reservations = models.IntegerField(default=3)

    @abstractmethod
    def get_active_user_reservations(self):
        raise NotImplementedError

    def can_make_new_reservation(self):
        return len(
            self.get_active_user_reservations().filter(event=None, special=False)) < self.max_number_of_reservations

    @staticmethod
    def get_quota_by_machine(machine_type, user):
        return Reservation.get_reservation_type(machine_type)(user=user).get_quota()

    class Meta:
        permissions = (
            ("can_create_event_reservation", "Can create event reservation"),
            ("can_edit_quota", "Can edit quotas"),
        )


class Quota3D(Quota):
    can_print = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def get_active_user_reservations(self):
        return self.user.reservation3d_set.filter(end_time__gte=timezone.now())

    @staticmethod
    def get_quota(user):
        return user.quota3d if hasattr(user, "quota3d") else Quota3D.objects.create(user=user)

    def __str__(self):
        return "User " + self.user.username + ", can " + "not " * (not self.can_print) + "print"


class QuotaSewing(Quota):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def get_active_user_reservations(self):
        return self.user.reservationsewing_set.filter(end_time__gte=timezone.now())

    @staticmethod
    def get_quota(user):
        return user.quotasewing if hasattr(user, "quotasewing") else QuotaSewing.objects.create(user=user)


class Penalty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_date = models.DateTimeField(auto_now_add=True)
    removed_date = models.DateTimeField()
