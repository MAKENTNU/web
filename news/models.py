from datetime import date, time
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from web.multilingual.database import MultiLingualTextField, MultiLingualRichTextUploadingField
from web.multilingual.widgets import MultiLingualTextarea


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
    title = MultiLingualTextField(
        max_length=100,
        verbose_name=_('Title'),
    )
    content = MultiLingualRichTextUploadingField()
    clickbait = MultiLingualTextField(
        max_length=300,
        verbose_name=_('Clickbait'),
        blank=True,
        widget=MultiLingualTextarea
    )
    image = models.ImageField(
        verbose_name=_('Image'),
    )
    contain = models.BooleanField(
        default=False,
        verbose_name=_("Don't crop the image"),
    )
    featured = models.BooleanField(
        default=True,
        verbose_name=_('Highlighted'),
    )
    hidden = models.BooleanField(
        default=False,
        verbose_name=_('Hidden'),
    )
    private = models.BooleanField(
        default=False,
        verbose_name=_('MAKE internal'),
    )

    def __str__(self):
        return self.title.__str__()

    class Meta:
        permissions = (
            ("can_view_private", "Can view private news"),
        )


class Article(NewsBase):
    objects = ArticleManager()
    pub_date = models.DateField(
        default=date.today,
        verbose_name=_('Publishing date'),
    )
    pub_time = models.TimeField(
        default=time.min,
        verbose_name=_('Publishing time'),
    )

    class Meta:
        ordering = (
            '-pub_date',
        )


class Event(NewsBase):
    multiday = models.BooleanField(default=False, verbose_name=_('Single registration'))
    hoopla = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hoopla url'),
    )
    number_of_tickets = models.IntegerField(verbose_name=_("Number of available tickets"), default=0)

    def get_future_occurrences(self):
        return TimePlace.objects.future().filter(event=self).order_by("start_date", "start_time")

    def get_past_occurrences(self):
        return TimePlace.objects.past().filter(event=self).order_by("-start_date", "-start_time")

    def number_of_registered_tickets(self):
        return self.eventticket_set.filter(active=True).count()


class TimePlace(models.Model):
    objects = TimePlaceManager()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    pub_date = models.DateField(
        default=date.today,
        verbose_name=_('Publishing date'),
    )
    pub_time = models.TimeField(
        default=time.min,
        verbose_name=_('Publishing time'),
    )
    start_date = models.DateField(
        default=date.today,
        verbose_name=_('Start date'),
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('End date')
    )
    start_time = models.TimeField(
        default=time.min,
        verbose_name=_('Start time'),
    )
    end_time = models.TimeField(
        default=time.min,
        verbose_name=_('End time'),
    )
    place = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Location'),
    )
    place_url = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Location URL'),
    )
    hoopla = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hoopla url'),
    )
    hidden = models.BooleanField(
        default=True,
        verbose_name=_('Hidden'),
    )
    number_of_tickets = models.IntegerField(verbose_name=_("Number of available tickets"), default=0)

    def __str__(self):
        return '%s - %s' % (self.event.title, self.start_date.strftime('%Y.%m.%d'))

    class Meta:
        ordering = (
            'start_date',
        )

    def number_of_registered_tickets(self):
        return self.eventticket_set.filter(active=True).count()


class EventTicket(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("User"))
    name = models.CharField(max_length=128, verbose_name=_("Name"))
    email = models.EmailField(verbose_name=_("Email"))
    active = models.BooleanField(verbose_name=_("Active"))
    comment = models.TextField(verbose_name=_("Comment"))
    # Since timeplaces can be added/removed from multiday events, it is easier to use two foreign keys, instead of
    # using a many-to-many field for timeplaces
    timeplace = models.ForeignKey(TimePlace, on_delete=models.CASCADE, blank=True, null=True,
                                  verbose_name=_("Timeplace"))
    event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Event"))
