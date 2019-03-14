from django.contrib.auth.models import User
from django.forms import ModelForm, TextInput
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
        self.fields["user"].label_from_instance = lambda user: user.get_full_name()


class EditMemberForm(ModelForm):
    class Meta:
        model = Member
        fields = "__all__"
        exclude = ["user", "date_joined", "date_quit", "quit", "reason_quit", "retired"]

        widgets = {
            "comment": TextInput(),
            "committees": SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)
        if not user.has_perm("internal.can_edit_group_membership"):
            for field_name in ["committees", "role", "comment", "guidance_exemption", "active", "honorary"]:
                del self.fields[field_name]
