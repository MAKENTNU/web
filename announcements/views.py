from django.views.generic import ListView

from announcements.models import Announcement


class AnnouncementAdminView(ListView):
    model = Announcement
    template_name = "announcements/announcements-admin.html"
