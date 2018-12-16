from django.forms import ModelForm

from news.models import TimePlace
from web.widgets import MazemapSearchInput, SemanticSearchableChoiceInput


class TimePlaceForm(ModelForm):
    class Meta:
        model = TimePlace
        fields = '__all__'
        exclude = []
        widgets = {
            "place": MazemapSearchInput(url_field="place_url"),
            "event": SemanticSearchableChoiceInput(),
        }
