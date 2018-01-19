from datetime import time

from django.db import models
from ckeditor.fields import RichTextField
from django.db.models import Q
from django.utils import timezone


def time_now(): timezone.now().time()


class ArticleManager(models.Manager):
    def published(self):
        return self.filter(
            Q(pub_date=timezone.now().date(), pub_time__lt=timezone.now().time()) |
            Q(pub_date__lt=timezone.now().date()))


class EventManager(ArticleManager):
    pass


class Article(models.Model):
    objects = ArticleManager()
    title = models.CharField(
        max_length=100,
        verbose_name='Tittel',
    )
    content = RichTextField()
    clickbait = models.TextField(
        max_length=300,
        verbose_name='Clickbait',
        blank=True,
    )
    image = models.ImageField(
        verbose_name='Bilde',
    )
    contain = models.BooleanField(
        default=False,
        verbose_name='Ikke crop bildet',
    )
    pub_date = models.DateField(
        default=timezone.now,
        verbose_name='Publiseringsdato',
    )
    pub_time = models.TimeField(
        default=time_now,
        blank=True,
        null=True,
        verbose_name='Publiseringstid',
    )
    hidden = models.BooleanField(
        default=False,
        verbose_name='Skjult',
    )
    private = models.BooleanField(
        default=False,
        verbose_name='Privat',
    )

    class Meta:
        ordering = (
            '-pub_date',
        )

    def __str__(self):
        return self.title


class Event(Article):
    objects = EventManager()
    start_date = models.DateField(
        default=timezone.now,
        verbose_name='Start-dato',
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Slutt-dato'
    )
    start_time = models.TimeField(
        default=time.min,
        verbose_name='Start-tidspunkt',
    )
    end_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name='Slutt-tidspunkt'
    )
    place = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Sted',
    )
    place_url = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Sted URL',
    )
    hoopla = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Hoopla url',
    )
