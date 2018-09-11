import django.forms as forms


class SemanticTimeInput(forms.TimeInput):
    template_name = "web/forms/widgets/semantic_time.html"


class SemanticChoiceInput(forms.Select):
    template_name = "web/forms/widgets/semantic_select.html"
