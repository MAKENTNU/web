from abc import ABCMeta
from typing import Dict, Type

from django import forms
from django.db.models import Model
from django.utils.translation import gettext_lazy as _

from web.widgets import MazeMapSearchInput, SemanticDateTimeInput, SemanticFileInput, SemanticSearchableChoiceInput
from .models import Article, Event, EventTicket, NewsBase, TimePlace


class TimePlaceForm(forms.ModelForm):
    class Meta:
        model = TimePlace
        fields = '__all__'
        widgets = {
            'event': forms.HiddenInput(),
            'place': MazeMapSearchInput(url_field='place_url'),
            'start_time': SemanticDateTimeInput(end_calendar_name='end_time'),
            'end_time': SemanticDateTimeInput(start_calendar_name='start_time'),
            'publication_time': SemanticDateTimeInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time > end_time:
                error_message = _("The event cannot end before it starts.")
                code = 'invalid_relative_to_other_field'
                raise forms.ValidationError({
                    'start_time': forms.ValidationError(error_message, code=code),
                    'end_time': forms.ValidationError(error_message, code=code),
                })

        return cleaned_data


class NewsBaseForm(forms.ModelForm):
    class Meta(ABCMeta):
        model: Type[NewsBase]
        fields = '__all__'
        widgets = {
            'image': SemanticFileInput(),
        }
        help_texts: Dict[str, str]

        @staticmethod
        def get_help_texts(news_class: Type[NewsBase]) -> Dict[str, str]:
            the_type, content_help_text = None, None
            if news_class is Article:
                the_type = _("the article")
                content_help_text = _("The main content of the article.")
            elif news_class is Event:
                the_type = _("the event")
                content_help_text = _("The main description of the event.")
            return {
                'content': content_help_text,
                'clickbait': _("A short text designed to bait users into clicking {the_type}.").format(the_type=the_type),
                'featured': _("If selected, {the_type} may be shown on the front page.").format(the_type=the_type),
                'hidden': _("If selected, {the_type} will only be visible to admin users.").format(the_type=the_type),
                'private': _("If selected, {the_type} will only be visible to members of MAKE NTNU.").format(the_type=the_type),
            }


class ArticleForm(NewsBaseForm):
    class Meta(NewsBaseForm.Meta):
        model = Article
        widgets = {
            **NewsBaseForm.Meta.widgets,
            'publication_time': SemanticDateTimeInput(),
        }
        help_texts = NewsBaseForm.Meta.get_help_texts(model)


class EventForm(NewsBaseForm):
    class Meta(NewsBaseForm.Meta):
        model = Event
        help_texts = NewsBaseForm.Meta.get_help_texts(model)


class EventParticipantsSearchForm(forms.Form):
    search_string = forms.CharField(
        max_length=500,
        label=_("Search for users"),
        help_text=_("You can search for users' name, username and email."),
    )


class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventTicket
        fields = ('user', 'timeplace', 'event', 'language', 'comment')
        widgets = {
            'language': SemanticSearchableChoiceInput(),
            'comment': forms.Textarea(attrs={
                'cols': "40",
                'rows': "3",
                'placeholder': _("Here you can enter any requests or information you want to provide to the organizers."),
            }),
        }


class ToggleForm(forms.Form):
    instance: Model
    toggle_attr = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance')
        self.instance = instance
        super().__init__(*args, **kwargs)

    def clean_toggle_attr(self):
        toggle_attr = self.cleaned_data['toggle_attr']
        try:
            attr_value = getattr(self.instance, toggle_attr)
        except AttributeError:
            raise forms.ValidationError("No attribute found with this name")
        if type(attr_value) is not bool:
            raise forms.ValidationError("The attribute is not a boolean field, and is therefore not toggleable")

        return toggle_attr
