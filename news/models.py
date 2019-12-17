import uuid
from datetime import date, time

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.models import User
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
        verbose_name=_("Title"),
    )
    content = MultiLingualRichTextUploadingField(
        verbose_name=_("Content"),
    )
    clickbait = MultiLingualTextField(
        max_length=300,
        verbose_name=_('Clickbait'),
        widget=MultiLingualTextarea
    )
    image = models.ImageField(
        verbose_name=_("Image"),
    )
    contain = models.BooleanField(
        default=False,
        verbose_name=_("Don't crop the image"),
    )
    featured = models.BooleanField(
        default=True,
        verbose_name=_("Highlighted"),
    )
    hidden = models.BooleanField(
        default=False,
        verbose_name=_("Hidden"),
    )
    private = models.BooleanField(
        default=False,
        verbose_name=_("MAKE internal"),
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
        verbose_name=_("Publishing date"),
    )
    pub_time = models.TimeField(
        default=time.min,
        verbose_name=_("Publishing time"),
    )

    class Meta:
        ordering = (
            '-pub_date',
        )


class Event(NewsBase):
    REPEATING = "R"
    STANDALONE = "S"

    EVENT_TYPE_CHOICES = (
        (REPEATING, _("Repeating")),
        (STANDALONE, _("Standalone")),
    )

    event_type = models.CharField(
        choices=EVENT_TYPE_CHOICES,
        max_length=1,
        default=REPEATING,
        verbose_name=_("Type of event")
    )
    number_of_tickets = models.IntegerField(verbose_name=_("Number of available tickets"), default=0)

    def get_future_occurrences(self):
        return TimePlace.objects.future().filter(event=self).order_by("start_date", "start_time")

    def get_past_occurrences(self):
        return TimePlace.objects.past().filter(event=self).order_by("-start_date", "-start_time")

    def number_of_registered_tickets(self):
        return self.eventticket_set.filter(active=True).count()

    @property
    def repeating(self):
        return self.event_type == self.REPEATING

    @property
    def standalone(self):
        return self.event_type == self.STANDALONE

    def can_register(self, user):
        if self.hidden:
            return False
        if self.private and not user.has_perm("news.can_view_private"):
            return False
        if self.standalone:
            return self.number_of_tickets > self.number_of_registered_tickets()
        return True


class TimePlace(models.Model):
    objects = TimePlaceManager()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    pub_date = models.DateField(
        default=date.today,
        verbose_name=_("Publishing date"),
    )
    pub_time = models.TimeField(
        default=time.min,
        verbose_name=_("Publishing time"),
    )
    start_date = models.DateField(
        default=date.today,
        verbose_name=_("Start date"),
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("End date")
    )
    start_time = models.TimeField(
        default=time.min,
        verbose_name=_("Start time"),
    )
    end_time = models.TimeField(
        default=time.min,
        verbose_name=_("End time"),
    )
    place = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Location"),
    )
    place_url = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Location URL"),
    )
    hidden = models.BooleanField(
        default=True,
        verbose_name=_("Hidden"),
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

    def can_register(self, user):
        if not self.event.can_register(user):
            return False
        return not self.hidden and self.number_of_registered_tickets() < self.number_of_tickets


class EventTicket(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("User"))
    # For backwards compatibility, name and email are no longer set. Getting name and email from user.
    _name = models.CharField(max_length=128, verbose_name=_("Name"), db_column="name")
    _email = models.EmailField(verbose_name=_("Email"), db_column="email")
    active = models.BooleanField(verbose_name=_("Active"), default=True)
    comment = models.TextField(verbose_name=_("Comment"), blank=True)
    language = models.CharField(max_length=2, choices=(("en", _("English")), ("nb", _("Norwegian"))), default="en",
                                verbose_name=_("Preferred language"))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    # Since timeplaces can be added/removed from standalone events, it is easier to use two foreign keys, instead of
    # using a many-to-many field for timeplaces
    timeplace = models.ForeignKey(TimePlace, on_delete=models.CASCADE, blank=True, null=True,
                                  verbose_name=_("Timeplace"))
    event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Event"))

    def __str__(self):
        return f"{self.name} - {self.event if self.event is not None else self.timeplace}"

    class Meta:
        permissions = (
            ("cancel_ticket", "Can cancel and reactivate all event tickets"),
        )

    @property
    def name(self):
        """
        Gets the name of the user whom the ticket is registered to. For backwards compatibility it returns the _name
        field if the user is not set.
        """
        return self.user.get_full_name() if self.user else self._name

    @property
    def email(self):
        """
        Gets the email of the user whom the ticket is registered to. For backwards compatibility it returns the _email
        field if the user is not set.
        """
        return self.user.email if self.user else self._email
