from django.db import models
from django.contrib.auth.models import User


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


class Quota3D(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    can_print = models.BooleanField(default=False)
    max_time_reservation = models.FloatField(default=0)
    max_number_of_reservations = models.IntegerField(default=0)


class Penalty3D(models.Model):
    user_quota = models.ForeignKey(Quota3D, on_delete=models.CASCADE)
    from_date = models.DateTimeField(auto_now_add=True)
    removed_date = models.DateTimeField()
