import django.forms as forms
from django.utils.translation import gettext_lazy as _


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
    template_name = "web/forms/widgets/mazemap_search.html"

    def __init__(self, campus_id=1, max_results=5, url_field=None, attrs=None):
        super().__init__(attrs=attrs)
        self.campus_id = campus_id
        self.max_results = max_results
        self.url_field = url_field

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"].update({
            "campus_id": self.campus_id,
            "max_results": self.max_results,
            "url_field": self.url_field,
        })
        return context
