from django import forms
from django.db.models.functions import Concat
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from js_asset import JS

from users.models import User
from web.widgets import SemanticChoiceInput, SemanticSearchableChoiceInput
from ..formfields import UserModelChoiceField
from ..models.machine import MachineType
from ..models.reservation import Quota


class QuotaForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset=User.objects.order_by(Concat("first_name", "last_name"), "username"),
        widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
        # `capfirst()` to avoid duplicate translation differing only in case
        label=capfirst(_("user")),
        required=False,
    )
    machine_type = forms.ModelChoiceField(
        queryset=MachineType.objects.order_by("priority"),
        label=capfirst(_("machine type")),
        empty_label=_("Select machine type"),
        widget=SemanticChoiceInput,
    )

    class Meta:
        model = Quota
        fields = "__all__"

    class Media:
        js = [
            JS("make_queue/js/quota_form.js", attrs={"defer": True}),
        ]

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        all_users = cleaned_data.get("all")

        user_error_message = None
        if not user and not all_users:
            user_error_message = _("User must be set when “All users” is not set.")
        if user and all_users:
            user_error_message = _("User cannot be set when “All users” is set.")

        if user_error_message:
            # Can't raise ValidationError when adding errors for both a specific field and the whole form (field=None)
            self.add_error("user", user_error_message)
            self.add_error(None, _("Must select either specific user or all users."))
            return

        return cleaned_data


class AdminQuotaPanelQueryForm(forms.Form):
    user = forms.ModelChoiceField(
        User.objects.all(),
        error_messages={"invalid_choice": "User with pk=%(value)s was not found."},
    )
