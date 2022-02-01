from abc import ABCMeta
from typing import Type

from django import forms
from django.utils.translation import gettext_lazy as _

from web.widgets import MazeMapSearchInput, SemanticDateTimeInput, SemanticFileInput, SemanticSearchableChoiceInput
from .models import Article, Event, EventTicket, NewsBase, TimePlace


class TimePlaceForm(forms.ModelForm):
    class Meta:
        model = TimePlace
        fields = '__all__'
        widgets = {
            'place': MazeMapSearchInput(url_field='place_url'),
            'event': SemanticSearchableChoiceInput(),
            'start_time': SemanticDateTimeInput(attrs={'end_calendar': 'end_time'}),
            'end_time': SemanticDateTimeInput(attrs={'start_calendar': 'start_time'}),
            'publication_time': SemanticDateTimeInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time > end_time:
                raise forms.ValidationError(_("The event cannot end before it starts"))

        return cleaned_data


class NewsBaseForm(forms.ModelForm):
    class Meta(ABCMeta):
        model: Type[NewsBase]
        fields = '__all__'
        widgets = {
            'image': SemanticFileInput(),
        }
        help_texts: dict

        @staticmethod
        def get_help_texts(news_class: Type[NewsBase]):
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

class EventsSearchForm(forms.Form):
    name = forms.CharField(label=_("Search for user"), max_length=500)

class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventTicket
        fields = ('comment', 'language')
        widgets = {
            'language': SemanticSearchableChoiceInput(),
            'comment': forms.Textarea(attrs={
                'cols': "40",
                'rows': "3",
                'placeholder': _(
                    "Here you can enter any requests or information you want to provide to the organizers"),
            }),
        }
