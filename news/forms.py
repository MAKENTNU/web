from django import forms
from django.utils.translation import gettext_lazy as _

from web.widgets import MazemapSearchInput, SemanticDateTimeInput, SemanticFileInput, SemanticSearchableChoiceInput
from .models import Article, Event, EventTicket, TimePlace


class TimePlaceForm(forms.ModelForm):
    class Meta:
        model = TimePlace
        fields = '__all__'
        widgets = {
            'place': MazemapSearchInput(url_field='place_url'),
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


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "publication_time": SemanticDateTimeInput(),
            "image": SemanticFileInput(),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = "__all__"
        widgets = {
            "image": SemanticFileInput(),
        }


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
