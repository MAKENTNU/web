import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.models import User
from util.locale_utils import short_date_format
from util.modelfields import CompressedImageField
from util.storage import OverwriteStorage, UploadToUtils
from web.modelfields import URLTextField, UnlimitedCharField
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField
from web.multilingual.widgets import MultiLingualTextarea


class NewsBaseQuerySet(models.QuerySet):

    def visible_to(self, user: User):
        hidden_news_query = Q(hidden=False)
        if not user.has_perm('news.can_view_private'):
            hidden_news_query &= Q(private=False)
        return self.filter(hidden_news_query)


def news_subclass_directory_path(instance: 'NewsBase', filename: str):
    model_name = instance._meta.model_name
    return f"news/{model_name}s/{filename}"


class NewsBase(models.Model):
    """
    The abstract class that contains the common fields and methods of ``Article`` and ``Event``.

    (Several of the fields' ``help_text`` arguments are defined in ``NewsBaseForm``, to facilitate customizing them to fit the two subclasses.)
    """
    title = MultiLingualTextField(verbose_name=_("Title"))
    content = MultiLingualRichTextUploadingField(verbose_name=_("Content"))
    clickbait = MultiLingualTextField(verbose_name=_("Clickbait"), widget=MultiLingualTextarea)
    image = CompressedImageField(upload_to=UploadToUtils.get_pk_prefixed_filename_func(news_subclass_directory_path),
                                 max_length=200, storage=OverwriteStorage(), verbose_name=_("Image"))
    image_description = MultiLingualTextField(verbose_name=_("image description"),
                                              help_text=_("This should be a concise visual description of the image,"
                                                          " which is mainly useful for people using a screen reader."))
    contain = models.BooleanField(default=False, verbose_name=_("Don't crop the image"))
    featured = models.BooleanField(default=True, verbose_name=_("Featured"))
    hidden = models.BooleanField(default=False, verbose_name=_("Hidden"))
    private = models.BooleanField(default=False, verbose_name=_("Internal"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    objects = NewsBaseQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.title)


class ArticleQuerySet(NewsBaseQuerySet):

    def published(self):
        return self.filter(hidden=False, publication_time__lte=timezone.localtime())


class Article(NewsBase):
    publication_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("Publication time"))

    objects = ArticleQuerySet.as_manager()

    class Meta(NewsBase.Meta):
        permissions = (
            ('can_view_private', "Can view private articles"),
        )
        ordering = ('-publication_time',)


class EventQuerySet(NewsBaseQuerySet):

    def future(self):
        return self.filter(
            timeplaces__end_time__gt=timezone.localtime()
        ).distinct()  # remove duplicates that can appear when filtering on values across tables

    def past(self):
        now = timezone.localtime()
        return self.filter(
            # Any repeating event with at least one timeplace that's already ended...
            Q(event_type=Event.Type.REPEATING, timeplaces__end_time__lte=now)
            # ...or any standalone event with timeplaces [this predicate is completed by the `exclude()` call below]...
            | Q(event_type=Event.Type.STANDALONE, timeplaces__isnull=False)
        ).exclude(
            # ...but exclude standalone events with at least one timeplace that has not ended
            Q(event_type=Event.Type.STANDALONE, timeplaces__end_time__gt=now)
        ).distinct()  # remove duplicates that can appear when filtering on values across tables


class Event(NewsBase):
    class Type(models.TextChoices):
        REPEATING = 'R', _("Repeating")
        STANDALONE = 'S', _("Standalone")

    event_type = models.CharField(
        choices=Type.choices,
        max_length=1,
        default=Type.REPEATING,
        verbose_name=_("Type of event"),
    )
    number_of_tickets = models.IntegerField(default=0, verbose_name=_("Number of available tickets"))

    objects = EventQuerySet.as_manager()

    class Meta(NewsBase.Meta):
        permissions = (
            ('can_view_private', "Can view private events"),
        )

    def get_future_occurrences(self):
        return self.timeplaces.published().future().order_by('start_time')

    def get_past_occurrences(self):
        return self.timeplaces.published().past().order_by('-start_time')

    @property
    def number_of_active_tickets(self):
        return self.tickets.filter(active=True).count()

    @property
    def repeating(self):
        return self.event_type == self.Type.REPEATING

    @property
    def standalone(self):
        return self.event_type == self.Type.STANDALONE

    def can_register(self, user):
        # When hidden, registration is always disabled
        if self.hidden:
            return False

        # Registration for private events is never allowed for non members
        if self.private and not user.has_perm('news.can_view_private'):
            return False

        # If there are no future occurrences, there is never anything to register for
        if not self.get_future_occurrences():
            return False

        # If the event is standalone, the ability to register is dependent on if there are any more available tickets
        if self.standalone:
            return self.number_of_active_tickets < self.number_of_tickets

        # Registration to a repeating event with future occurrences is handled by the time place objects
        return True


class TimePlaceQuerySet(models.QuerySet):

    def published(self):
        return self.filter(hidden=False, event__hidden=False, publication_time__lte=timezone.now())

    def unpublished(self):
        return self.filter(Q(hidden=True) | Q(event__hidden=True) | Q(publication_time__gt=timezone.now()))

    def future(self):
        return self.filter(end_time__gt=timezone.now())

    def past(self):
        return self.filter(end_time__lte=timezone.now())


class TimePlace(models.Model):
    event = models.ForeignKey(
        to=Event,
        on_delete=models.CASCADE,
        related_name='timeplaces',
    )
    publication_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("Publication time"))
    start_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("Start time"))
    end_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("End time"))
    place = UnlimitedCharField(blank=True, verbose_name=_("Location"))
    place_url = URLTextField(blank=True, verbose_name=_("Location URL"))
    hidden = models.BooleanField(default=True, verbose_name=_("Hidden"))
    number_of_tickets = models.IntegerField(default=0, verbose_name=_("Number of available tickets"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    objects = TimePlaceQuerySet.as_manager()

    class Meta:
        ordering = ('start_time',)

    def __str__(self):
        return f"{self.event.title} - {short_date_format(self.start_time)}"

    @property
    def number_of_active_tickets(self):
        return self.tickets.filter(active=True).count()

    def is_in_the_past(self):
        return self.end_time < timezone.localtime()

    def can_register(self, user):
        if not self.event.can_register(user) or self.is_in_the_past():
            return False
        return not self.hidden and self.number_of_active_tickets < self.number_of_tickets


class EventTicket(models.Model):
    class Language(models.TextChoices):
        ENGLISH = 'en', _("English")
        NORWEGIAN = 'nb', _("Norwegian")

    user = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_tickets',
        verbose_name=_("User"),
    )
    # Since timeplaces can be added/removed from standalone events, it is easier to use two foreign keys, instead of
    # using a many-to-many field for timeplaces
    timeplace = models.ForeignKey(
        to=TimePlace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=_("Timeplace"),
    )
    event = models.ForeignKey(
        to=Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=_("Event"),
    )
    # For backwards compatibility, name and email are no longer set. Getting name and email from user.
    _name = models.CharField(max_length=128, db_column='name', verbose_name=_("Name"))
    _email = models.EmailField(db_column='email', verbose_name=_("Email"))
    active = models.BooleanField(default=True, verbose_name=_("Active"))
    comment = models.TextField(blank=True, verbose_name=_("Comment"))
    language = models.CharField(choices=Language.choices, max_length=2, default=Language.ENGLISH,
                                verbose_name=_("Preferred language"))
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        permissions = (
            ('cancel_ticket', "Can cancel and reactivate all event tickets"),
        )

    def __str__(self):
        return f"{self.name} - {self.event if self.event else self.timeplace}"

    @property
    def registered_event(self) -> Event:
        return self.event or self.timeplace.event

    @property
    def name(self):
        """
        Gets the name of the user whom the ticket is registered to.
        For backwards compatibility it returns the ``_name`` field if the user is not set.
        """
        return self.user.get_full_name() if self.user else self._name

    @property
    def email(self):
        """
        Gets the email of the user whom the ticket is registered to.
        For backwards compatibility it returns the ``_email`` field if the user is not set.
        """
        return self.user.email if self.user else self._email
