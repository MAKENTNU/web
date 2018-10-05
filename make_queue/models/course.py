from django.contrib.auth.models import User
from django.db import models


class Printer3DCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    username = models.CharField(max_length=32)
    date = models.DateField()
    card_number = models.IntegerField(null=True)
    name = models.CharField(max_length=256)
    registered = models.BooleanField(default=False)