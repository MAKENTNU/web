from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from announcements.forms import AnnouncementForm
from announcements.models import Announcement


class AnnouncementAdminView(PermissionRequiredMixin, ListView):
    model = Announcement
    template_name = "announcements/announcements_admin.html"
    context_object_name = "announcements"
    permission_required = (
        "announcements.change_announcement",
    )


class CreateAnnouncementView(PermissionRequiredMixin, CreateView):
    model = Announcement,
    template_name = "announcements/create_announcement.html"
    form_class = AnnouncementForm
    permission_required = (
        "announcements.add_announcement",
    )
    success_url = reverse_lazy("announcement_admin")


class EditAnnouncementView(PermissionRequiredMixin, UpdateView):
    model = Announcement
    template_name = "announcements/edit_announcement.html"
    form_class = AnnouncementForm
    permission_required = (
        "announcements.change_announcement",
    )
    success_url = reverse_lazy("announcement_admin")


class DeleteAnnouncementView(PermissionRequiredMixin, DeleteView):
    model = Announcement
    permission_required = (
        "announcements.delete_announcement",
    )
    success_url = reverse_lazy("announcement_admin")
