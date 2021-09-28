from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from mail import email
from web.multilingual.formfields import MultiLingualFormField, MultiLingualRichTextFormField
from web.multilingual.widgets import MultiLingualTextInput, MultiLingualRichTextUploading
from web.widgets import MazemapSearchInput, SemanticDateTimeInput, SemanticFileInput, SemanticSearchableChoiceInput
from .models import Article, Event, EventTicket, TimePlace


class TimePlaceForm(forms.ModelForm):
    class Meta:
        model = TimePlace
        fields = '__all__'
        widgets = {
            "place": MazemapSearchInput(url_field="place_url"),
            "event": SemanticSearchableChoiceInput(),
            "start_time": SemanticDateTimeInput(attrs={"end_calendar": "end_time"}),
            "end_time": SemanticDateTimeInput(attrs={"start_calendar": "start_time"}),
            "publication_time": SemanticDateTimeInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time > end_time:
            raise ValidationError(_("The event cannot end before it starts"))

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
        fields = ("comment", "language")
        widgets = {
            "language": SemanticSearchableChoiceInput(),
            "comment": forms.Textarea(attrs={
                "cols": "40",
                "rows": "3",
                "placeholder": _(
                    "Here you can enter any requests or information you want to provide to the organizers"),
            }),
        }


class EmailForm(forms.Form):
    event = forms.ModelChoiceField(required=False, queryset=Event.objects.all())
    time_place = forms.ModelChoiceField(required=False, queryset=TimePlace.objects.all())
    subject = MultiLingualFormField(required=True, max_length=190, widget=MultiLingualTextInput)
    body = MultiLingualRichTextFormField(required=True, widget=MultiLingualRichTextUploading)

    def clean(self):
        cleaned_data = super().clean()
        event = cleaned_data.get('event')
        time_place = cleaned_data.get('time_place')

        if not event and not time_place:
            raise forms.ValidationError("Event and timeplace cannot both be None.")
        if event and time_place:
            raise forms.ValidationError("Event and timeplace cannot both be set.")
        return cleaned_data

    def send_email(self):
        event = self.cleaned_data.get('event')
        time_place = self.cleaned_data.get('time_place')
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['body']

        event_or_time_place = event or time_place
        send_mail(
            subject,
            email.render_text({"body": body, "event_or_time_place": event_or_time_place},
                              text_template_name='email/reminder.txt'),
            settings.EMAIL_HOST_USER,
            [ticket.email for ticket in event_or_time_place.tickets.all().filter(active=True)],
            html_message=render_to_string('email/reminder.html',
                                          {"body": body, "event_or_time_place": event_or_time_place}
                                          )
        )
