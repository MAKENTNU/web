from django.forms import ModelForm

from news.models import TimePlace
from web.fields import MazemapSearchField
from web.widgets import MazemapSearchInput


class TimePlaceForm(ModelForm):
    def __init__(self, **kwargs):
        # self.place = MazemapSearchField(
        #    url_field="place_url",
        self.initial = kwargs["initial"].get("place", None)
        # self.place = MazemapSearchField(url_field="place_url")
        super().__init__(**kwargs)

    #place = MazemapSearchField(url_field="place_url")

    class Meta:
        model = TimePlace
        fields = '__all__'
        exclude = []
        widgets = {
            "place": MazemapSearchInput(
                url_field="place_url",
        #        initial=self.initial,
            )
        }
