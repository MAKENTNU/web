import logging
import sys
import uuid
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.models import User
from web.modelfields import URLTextField, UnlimitedCharField
from web.multilingual.modelfields import MultiLingualRichTextUploadingField, MultiLingualTextField
from web.multilingual.widgets import MultiLingualTextarea


class NewsBase(models.Model):
    title = MultiLingualTextField(verbose_name=_("Title"))
    content = MultiLingualRichTextUploadingField(verbose_name=_("Content"))
    clickbait = MultiLingualTextField(verbose_name=_("Clickbait"), widget=MultiLingualTextarea)
    image = models.ImageField(verbose_name=_("Image"))
    contain = models.BooleanField(default=False, verbose_name=_("Don't crop the image"))
    featured = models.BooleanField(default=True, verbose_name=_("Highlighted"))
    hidden = models.BooleanField(default=False, verbose_name=_("Hidden"))
    private = models.BooleanField(default=False, verbose_name=_("MAKE internal"))

    class Meta:
        permissions = (
            ('can_view_private', "Can view private news"),
        )

    def __str__(self):
        return str(self.title)

    def save(self, **kwargs):
        """
        Override of save, to change all JPEG images to have quality 90. This greatly reduces the size of JPEG images,
        while resulting in non to very minuscule reduction in quality. In almost all cases, the possible reduction in
        quality will not be visible to the naked eye.
        """
        # Only check the image if there is actually an image
        if self.image:
            # PIL will throw an IO error if it cannot open the image, or does not support the given format
            try:
                image = Image.open(self.image)
                if image.format == "JPEG":
                    output = BytesIO()
                    image.save(output, format="JPEG", quality=90)
                    output.seek(0)

                    self.image = InMemoryUploadedFile(output, "ImageField", self.image.name, "image/jpeg",
                                                      sys.getsizeof(output), None)
                # Should not close image, as Django uses the image and closes it by default
            except IOError as e:
                logging.getLogger('django.request').exception(e)

        super().save(**kwargs)


class ArticleQuerySet(models.QuerySet):

    def published(self):
        return self.filter(hidden=False, publication_time__lte=timezone.localtime())


class Article(NewsBase):
    publication_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("Publishing time"))

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ('-publication_time',)


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

    def get_future_occurrences(self):
        return self.timeplaces.future().order_by('start_time')

    def get_past_occurrences(self):
        return self.timeplaces.past().order_by('-start_time')

    def number_of_registered_tickets(self):
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
            return self.number_of_tickets > self.number_of_registered_tickets()

        # Registration to a repeating event with future occurrences is handled by the time place objects
        return True


class TimePlaceQuerySet(models.QuerySet):

    def published(self):
        return self.filter(hidden=False, event__hidden=False).filter(publication_time__lte=timezone.localtime())

    def future(self):
        return self.published().filter(end_time__gt=timezone.localtime())

    def past(self):
        return self.published().filter(end_time__lte=timezone.localtime())


class TimePlace(models.Model):
    event = models.ForeignKey(
        to=Event,
        on_delete=models.CASCADE,
        related_name='timeplaces',
    )
    publication_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("Publishing time"))
    start_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("Start time"))
    end_time = models.DateTimeField(default=timezone.localtime, verbose_name=_("End time"))
    place = UnlimitedCharField(blank=True, verbose_name=_("Location"))
    place_url = URLTextField(blank=True, verbose_name=_("Location URL"))
    hidden = models.BooleanField(default=True, verbose_name=_("Hidden"))
    number_of_tickets = models.IntegerField(default=0, verbose_name=_("Number of available tickets"))

    objects = TimePlaceQuerySet.as_manager()

    class Meta:
        ordering = ('start_time',)

    def __str__(self):
        return '%s - %s' % (self.event.title, self.start_time.strftime('%Y.%m.%d'))

    def number_of_registered_tickets(self):
        return self.tickets.filter(active=True).count()

    def is_in_the_past(self):
        return self.end_time < timezone.localtime()

    def can_register(self, user):
        if not self.event.can_register(user) or self.is_in_the_past():
            return False
        return not self.hidden and self.number_of_registered_tickets() < self.number_of_tickets


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
        return f"{self.name} - {self.event if self.event is not None else self.timeplace}"

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
