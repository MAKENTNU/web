from django.forms import ModelForm

from announcements.models import Announcement
from web.widgets import SemanticDateTimeInput, SemanticChoiceInput


class AnnouncementForm(ModelForm):
    class Meta:
        model = Announcement
        fields = "__all__"
        widgets = {
            "classification": SemanticChoiceInput(),
            "display_from": SemanticDateTimeInput(attrs={"end_calendar": "display_to"}),
            "display_to": SemanticDateTimeInput(attrs={"start_calendar": "display_from", "default_blank": True}),
        }
