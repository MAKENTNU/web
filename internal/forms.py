from django.contrib.auth.models import User
from django.forms import ModelForm, TextInput, CharField
from django.utils.translation import gettext_lazy as _

from internal.models import Member, SystemAccess
from web.widgets import SemanticSearchableChoiceInput, SemanticDateInput, SemanticMultipleSelectInput


class AddMemberForm(ModelForm):
    class Meta:
        model = Member
        fields = ["user", "date_joined", "committees"]
        widgets = {
            "user": SemanticSearchableChoiceInput(prompt_text=_("Choose user"), required=True),
            "date_joined": SemanticDateInput(),
            "committees": SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(member=None)
        self.fields["user"].label_from_instance = lambda user: user.get_full_name()


class EditMemberForm(ModelForm):
    card_number = CharField(max_length=10, min_length=10, empty_value="", label=_("Card number (EM)"))

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


class MemberQuitForm(ModelForm):
    class Meta:
        model = Member
        fields = ["date_quit", "reason_quit"]

        widgets = {
            "date_quit": SemanticDateInput(),
            "reason_quit": TextInput(),
        }


class ToggleSystemAccessForm(ModelForm):
    class Meta:
        model = SystemAccess
        fields = "__all__"

        widgets = {
            "name": SemanticSearchableChoiceInput(),
            "member": SemanticSearchableChoiceInput(),
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["name"].disabled = True
        self.fields["member"].disabled = True
        self.fields["member"].label_from_instance = lambda member: member.user.get_full_name()
