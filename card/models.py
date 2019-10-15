from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

import card.forms


class CardNumberField(models.CharField):
    """
    Custom field for card numbers, doing some extra validation
    """

    def __init__(self, **kwargs):
        kwargs = {
            "verbose_name": _("Card number"),
            **kwargs,
            "validators": card.forms.card_number_validators,
            "max_length": 10,
            "error_messages": {
                "unique": _("Card number already in use"),
            },
        }
        super().__init__(**kwargs)  # No card numbers are more than ten digits long

    def formfield(self, **kwargs):
        if "form_class" not in kwargs:
            kwargs["form_class"] = card.forms.CardNumberField
        return super().formfield(**kwargs)


class Card(models.Model):
    """
    Model for connecting a card number to a user
    """
    number = CardNumberField(unique=True, null=True)
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL, verbose_name=_("User"))

    def __str__(self):
        return f"EM {self.number}" if self.number else ""

    def __repr__(self):
        return f'<Card: {str(self)}, {self.user}>'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, update_course=True):
        """
        Saves the card object. If both number and user fields are None the object is deleted.
        An extra parameter update_course determines whether the connected Printer3DCourse object should be updated
        if there is a change in the user field. Defaults to True. Mainly for calls from Printer3DCourse save().
        """
        all_none = self.number is None and self.user is None
        is_creation = self.pk is None

        if all_none:
            if not is_creation:
                self.delete()  # Delete empty object
            return  # Do not create empty object

        if update_course and hasattr(self, "printer3dcourse"):
            if is_creation:
                self._update_course_user()
            else:
                old = Card.objects.get(pk=self.pk)
                if old.user != self.user:
                    self._update_course_user()

        super().save(force_insert, force_update, using, update_fields)

    def _update_course_user(self):
        self.printer3dcourse.user = self.user
        self.printer3dcourse.save()

    @classmethod
    def update_or_create(cls, number=None, user=None, update_course=True):
        """
        Checks if the user has a card already. Updates the card number if it has, creates a card if it hasn't.
        Raises ValidationError if card with number is already connected to another user
        :param user: The user whose card number to set
        :param number: The card number to attach to the user. Must be zero-padded and ten digits long or None.
        :param update_course: Whether to propagate changes to the connected Printer3DCourse. Defaults to True.
        :return: The updated or created card
        """
        if not user and not number:
            return None

        card_with_number = Card.objects.filter(number=number)
        if hasattr(user, 'card'):
            user.card.number = number
            user.card.save(update_course=False)
            return user.card
        elif card_with_number.filter(user__isnull=False).exists():
            raise ValidationError(_("Card number already in use"))
        elif card_with_number.exists():  # Card with number but no user
            card_with_number = card_with_number.first()
            card_with_number.user = user
            card_with_number.save(update_course)  # Update does not call save() or emit signals, thus not used here
            return card_with_number
        else:
            # There exists no card for user and no card with number, create a new card
            return cls.objects.create(user=user, number=number)

    @classmethod
    def is_valid(cls, value):
        """
        Checks if value is a valid card number by running all card number validators.
        :param value: The card number to check
        :return: True if value passes all validators
        """
        for validator in card.forms.card_number_validators:
            try:
                validator(value)
            except ValidationError:
                return False
        return True
