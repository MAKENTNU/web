from django.forms import ModelForm

from announcements.models import Announcement
from web.widgets import SemanticChoiceInput, SemanticDateTimeInput


class AnnouncementForm(ModelForm):
    class Meta:
        model = Announcement
        fields = "__all__"
        widgets = {
            "classification": SemanticChoiceInput(),
            "display_from": SemanticDateTimeInput(end_calendar_name="display_to"),
            "display_to": SemanticDateTimeInput(
                start_calendar_name="display_from", default_blank=True
            ),
        }
