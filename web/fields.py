from django.forms import CharField

from web.widgets import MazemapSearchInput


class MazemapSearchField(CharField):
    def __init__(self, **kwargs):
        self.widget = MazemapSearchInput(attrs={
            kwargs.pop("campus_id", 1),
            kwargs.pop("max_results", 5),
            kwargs.pop("name", "mazemap_place_field"),
            kwargs.pop("url_field", None),
            kwargs.pop("initial", None),
        })
        super().__init__(**kwargs)
