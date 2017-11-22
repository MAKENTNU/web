from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from abc import abstractmethod


class Machine(models.Model):
    status_choices = (
        ("R", "Reserved"),
        ("F", "Free"),
        ("I", "In use"),
        ("O", "Out of order"),
        ("M", "Maintenance"),
    )

    status = models.CharField(max_length=2, choices=status_choices)
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=40)
    model = models.CharField(max_length=40)

    @abstractmethod
    def get_reservation_set(self):
        pass

    @abstractmethod
    def can_user_use(self, user):
        pass

    def reservations_in_period(self, start_time, end_time):
        return self.get_reservation_set().filter(start_time__lt=start_time, end_time__gt=start_time) | \
               self.get_reservation_set().filter(start_time__gte=start_time, end_time__lte=end_time) | \
               self.get_reservation_set().filter(start_time__lt=end_time, start_time__gt=start_time,
                                                 end_time__gte=end_time)


class Printer3D(Machine):
    def can_user_use(self, user):
        return user.quota3d.can_print

    def get_reservation_set(self):
        return self.reservation3d_set


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event = models.BooleanField(default=False)
    showed = models.NullBooleanField(default=None)

    @abstractmethod
    def get_quota(self):
        pass

    def save(self, *args, **kwargs):
        if not self.validate():
            raise ValidationError("Not a valid reservation")
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
        if self.start_time > self.end_time:
            return False

        # Event reservations are always valid, if the time is not already reserved
        if self.event:
            return self.user.has_perm("make_queue.can_create_event_reservation")

        # Check if the reservation is shorter than the maximum duration allowed for the user
        if self.end_time - self.start_time > timedelta(hours=self.get_quota().max_time_reservation):
            return False

        # If a primary key is set, the reservation is already saved once, and does not
        return self.pk is not None or self.get_quota().can_make_new_reservation()

    class Meta:
        abstract = True


class Reservation3D(Reservation):
    def get_quota(self):
        return self.user.quota3d


class Quota(models.Model):
    max_time_reservation = models.FloatField(default=0)
    max_number_of_reservations = models.IntegerField(default=0)

    @abstractmethod
    def get_active_user_reservations(self):
        pass

    def can_make_new_reservation(self):
        return len(self.get_active_user_reservations().filter(event=False)) < self.max_number_of_reservations

    class Meta:
        permissions = (
            ("can_create_event_reservation", "Can create event reservation"),
        )


class Quota3D(Quota):
    can_print = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def get_active_user_reservations(self):
        return self.user.reservation3d_set.filter(end_time__gte=timezone.now())


class Penalty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_date = models.DateTimeField(auto_now_add=True)
    removed_date = models.DateTimeField()