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
