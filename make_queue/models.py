from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


class Printer3D(models.Model):
    status_choices = (
        ("R", "Reserved"),
        ("F", "Free"),
        ("I", "In use"),
        ("O", "Out of order"),
        ("M", "Maintenance"),
    )
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=40)
    status = models.CharField(max_length=2, choices=status_choices)


class Reservation3D(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    printer = models.ForeignKey(Printer3D, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event = models.BooleanField(default=False)
    showed = models.NullBooleanField(default=None)

    def save(self, *args, **kwargs):
        if not self.validate():
            raise ValidationError
        super(Reservation3D, self).save(*args, **kwargs)

    # A reservation should not be able to be moved, only extended
    def validate(self):
        # Check if the printer is already reserved for the given duration
        if self.printer.reservation3d_set.filter(start_time__gt=self.start_time, end_time__lt=self.end_time).exists():
            return False

        # Event reservations are always valid, if the time is not already reserved
        if self.event:
            return True

        # Check if the reservation is shorter than the maximum duration allowed for the user
        if self.end_time - self.start_time > timedelta(hours=self.user.quota3d.max_time_reservation):
            return False

        # If a primary key is set, the reservation is already saved once, and does not
        return self.pk is not None or self.user.quota3d.can_make_new_reservation()


class Quota3D(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    can_print = models.BooleanField(default=False)
    max_time_reservation = models.FloatField(default=0)
    max_number_of_reservations = models.IntegerField(default=0)

    def get_active_user_reservations(self):
        return self.user.reservation3d_set.filter(end_time__gte=datetime.now())

    def can_make_new_reservation(self):
        return len(self.get_active_user_reservations().filter(event=False)) < self.max_number_of_reservations


class Penalty3D(models.Model):
    user_quota = models.ForeignKey(Quota3D, on_delete=models.CASCADE)
    from_date = models.DateTimeField(auto_now_add=True)
    removed_date = models.DateTimeField()
