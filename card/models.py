from django.contrib.auth.models import User
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _


class Card(models.Model):
    number = models.fields.CharField(max_length=16, verbose_name=_("Card number"))
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))

    class Meta:
        constraints = (
            UniqueConstraint(fields=['number'], name='unique_number'),
        )

    def __str__(self):
        return self.number

    @classmethod
    def update_or_create(cls, user, number):
        if hasattr(user, 'card'):
            user.card.number = number
            user.card.save()
        else:
            cls.objects.create(user=user, number=number)
