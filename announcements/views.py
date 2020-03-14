from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from announcements.models import Announcement


class AnnouncementAdminView(PermissionRequiredMixin, ListView):
    model = Announcement
    template_name = "announcements/announcements-admin.html"
    context_object_name = "announcements"
    permission_required = (
        "announcements.change_announcement",
    )
