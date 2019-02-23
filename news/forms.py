from django.forms import ModelForm, Textarea
from django.utils.translation import gettext_lazy as _

from news.models import Event
from news.models import TimePlace, EventTicket, Article
from web.widgets import MazemapSearchInput, SemanticSearchableChoiceInput, SemanticTimeInput, SemanticDateInput
from web.widgets import SemanticFileInput


class TimePlaceForm(ModelForm):
    class Meta:
        model = TimePlace
        fields = '__all__'
        exclude = ["hoopla"]
        widgets = {
            "place": MazemapSearchInput(url_field="place_url"),
            "event": SemanticSearchableChoiceInput(),
            "start_time": SemanticTimeInput(),
            "start_date": SemanticDateInput(),
            "end_time": SemanticTimeInput(),
            "end_date": SemanticDateInput(),
            "pub_time": SemanticTimeInput(),
            "pub_date": SemanticDateInput(),
        }


class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        exclude = []
        widgets = {
            "pub_time": SemanticTimeInput(),
            "pub_date": SemanticDateInput(),
            "image": SemanticFileInput(),
        }


class EventRegistrationForm(ModelForm):
    class Meta:
        model = EventTicket
        fields = "__all__"
        exclude = ["user", "active", "timeplace", "event"]
        widgets = {
            "language": SemanticSearchableChoiceInput(),
            "comment": Textarea(attrs={
                "cols": "40",
                "rows": "3",
                "placeholder": _("Here you can enter any requests or information you want to provide to the organizers")
            })
        }


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = "__all__"
        exclude = ["hoopla"]
        widgets = {
            "image": SemanticFileInput()
        }
