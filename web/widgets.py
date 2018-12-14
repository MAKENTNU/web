import django.forms as forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy


class SemanticTimeInput(forms.TimeInput):
    template_name = "web/forms/widgets/semantic_time.html"


class SemanticChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_select.html"


class SemanticSearchableChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_search_select.html"
    prompt_text = _("Choose value")

    def __init__(self, *args, **kwargs):
        super().__init__()
        if "prompt_text" in kwargs:
            self.attrs["prompt_text"] = kwargs["prompt_text"]
        else:
            self.attrs["prompt_text"] = self.prompt_text


class SemanticDateInput(forms.DateInput):
    template_name = "web/forms/widgets/semantic_date.html"


class MazemapSearchInput(forms.TextInput):
    """
    Widget that enables mazemap search functionality, including autofill of url to mazemap
    """
    template_name = "web/forms/widgets/mazemap_search.html"

    class Media:
        js = ('web/js/mazemap-search.js', reverse_lazy("javascript-catalog"))

    def __init__(self, campus_id=1, max_results=5, url_field=None, attrs=None):
        """
        :param campus_id: Campus to search for points of interest on. Default: NTNU Gløshaugen
        :param max_results: Maximum number of search results to return
        :param url_field: Field to autofill with mazemap url. If None, autofill functionality is turned off
        :param attrs: HTML attributes for the <input> element
        """

        default_attrs = {
            "placeholder": _("Search places"),
            "data-campusId": campus_id,
            "data-maxResults": max_results,
            "data-urlField": url_field,
        }
        required_class_attr = "prompt"

        if attrs:
            default_attrs.update(attrs)

        default_attrs["class"] = default_attrs.get("class", "") + " " + required_class_attr

        super().__init__(attrs=default_attrs)
