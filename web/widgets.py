import django.forms as forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


class SemanticTimeInput(forms.TimeInput):
    template_name = "web/forms/widgets/semantic_time.html"


class SemanticDateInput(forms.DateInput):
    template_name = "web/forms/widgets/semantic_date.html"


class SemanticDateTimeInput(forms.DateTimeInput):
    template_name = "web/forms/widgets/semantic_datetime.html"


class SemanticChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_select.html"


class SemanticSearchableChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_search_select.html"
    prompt_text = _("Choose value")

    def __init__(self, *args, **kwargs):
        super().__init__(attrs=kwargs.pop("attrs", {}))
        self.attrs["prompt_text"] = kwargs.pop("prompt_text", self.prompt_text)
        self.attrs["force_selection"] = kwargs.pop("force_selection", False)


class SemanticMultipleSelectInput(forms.SelectMultiple):
    template_name = "web/forms/widgets/semantic_select_multiple.html"
    prompt_text = _("Choose value")

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.attrs["prompt_text"] = kwargs.pop("prompt_text", self.prompt_text)


class SemanticFileInput(forms.ClearableFileInput):
    template_name = "web/forms/widgets/semantic_file.html"


class MazemapSearchInput(forms.TextInput):
    """
    Widget that enables MazeMap search functionality, including autofill of URL to MazeMap.
    """
    template_name = "web/forms/widgets/mazemap_search.html"
    required_class_attr = "prompt"
    placeholder = _("Search places")

    class Media:
        js = ("web/js/forms/widgets/mazemap_search.js",)

    def __init__(self, campus_id=1, max_results=5, url_field=None, attrs=None):
        """
        :param campus_id: Campus to search for points of interest on. Default: NTNU Gløshaugen
        :param max_results: Maximum number of search results to return
        :param url_field: Field to autofill with MazeMap URL. If None, autofill functionality is turned off
        :param attrs: HTML attributes for the <input> element
        """

        default_attrs = {
            "placeholder": self.placeholder,
            "data-campusId": campus_id,
            "data-maxResults": max_results,
            "data-urlField": url_field,
        }
        if attrs:
            default_attrs.update(attrs)

        default_attrs["class"] = f"{default_attrs.get('class', '')} {self.required_class_attr}"

        super().__init__(attrs=default_attrs)
