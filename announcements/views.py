from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from util.views import PreventGetRequestsMixin
from .forms import AnnouncementForm
from .models import Announcement


class AnnouncementAdminView(PermissionRequiredMixin, ListView):
    permission_required = ("announcements.change_announcement",)
    model = Announcement
    template_name = "announcements/announcements_admin.html"
    context_object_name = "announcements"


class CreateAnnouncementView(PermissionRequiredMixin, CreateView):
    permission_required = ("announcements.add_announcement",)
    model = Announcement
    form_class = AnnouncementForm
    template_name = "announcements/create_announcement.html"
    success_url = reverse_lazy("announcement_admin")


class EditAnnouncementView(PermissionRequiredMixin, UpdateView):
    permission_required = ("announcements.change_announcement",)
    model = Announcement
    form_class = AnnouncementForm
    template_name = "announcements/edit_announcement.html"
    success_url = reverse_lazy("announcement_admin")


class DeleteAnnouncementView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ("announcements.delete_announcement",)
    model = Announcement
    success_url = reverse_lazy("announcement_admin")
