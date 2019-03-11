from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from internal.models import Member
from web.widgets import SemanticSearchableChoiceInput, SemanticDateInput, SemanticMultipleSelectInput


class AddMemberForm(ModelForm):
    class Meta:
        model = Member
        fields = ["user", "date_joined", "committees"]
        widgets = {
            "user": SemanticSearchableChoiceInput(prompt_text=_("Choose user")),
            "date_joined": SemanticDateInput(),
            "committees": SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(member=None)
