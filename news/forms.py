from django.forms import ModelForm, Textarea
from django.utils.translation import gettext_lazy as _

from news.models import TimePlace, EventTicket
from web.widgets import MazemapSearchInput, SemanticSearchableChoiceInput, SemanticTimeInput, SemanticDateInput


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
