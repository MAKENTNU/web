from datetime import time

from django.db import models
from ckeditor.fields import RichTextField
from django.db.models import Q
from django.utils import timezone


class ArticleManager(models.Manager):
    def published(self):
        return self.filter(hidden=False).filter(
            Q(pub_date=timezone.now().date(), pub_time__lt=timezone.now().time()) |
            Q(pub_date__lt=timezone.now().date()))


class TimePlaceManager(models.Manager):
    def published(self):
        return self.filter(hidden=False, event__hidden=False).filter(
            Q(pub_date=timezone.now().date(), pub_time__lt=timezone.now().time()) |
            Q(pub_date__lt=timezone.now().date()))

    def future(self):
        return self.published().filter(
            Q(start_date=timezone.now().date(), start_time__gt=timezone.now().time()) |
            Q(start_date__gt=timezone.now().date()))

    def past(self):
        return self.published().filter(
            Q(start_date=timezone.now().date(), start_time__lt=timezone.now().time()) |
            Q(start_date__lt=timezone.now().date()))


class NewsBase(models.Model):
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
    featured = models.BooleanField(
        default=False,
        verbose_name='Fremhevet',
    )
    hidden = models.BooleanField(
        default=False,
        verbose_name='Skjult',
    )
    private = models.BooleanField(
        default=False,
        verbose_name='MAKE intern',
    )

    def __str__(self):
        return self.title

    class Meta:
        permissions = (
            ("can_view_private", "Can view private news"),
        )


class Article(NewsBase):
    objects = ArticleManager()
    pub_date = models.DateField(
        default=timezone.now,
        verbose_name='Publiseringsdato',
    )
    pub_time = models.TimeField(
        default=time.min,
        verbose_name='Publiseringstid',
    )

    class Meta:
        ordering = (
            '-pub_date',
        )


class Event(NewsBase):
    multiday = models.BooleanField(default=False, verbose_name='Én påmelding')
    hoopla = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Hoopla url',
    )


class TimePlace(models.Model):
    objects = TimePlaceManager()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    pub_date = models.DateField(
        default=timezone.now,
        verbose_name='Publiseringsdato',
    )
    pub_time = models.TimeField(
        default=time.min,
        verbose_name='Publiseringstid',
    )
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
    hidden = models.BooleanField(
        default=True,
        verbose_name='Skjult',
    )

    def __str__(self):
        return '%s - %s' % (self.event.title, self.start_date.strftime('%Y.%m.%d'))

    class Meta:
        ordering = (
            'start_date',
        )
