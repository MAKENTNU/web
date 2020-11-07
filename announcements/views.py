from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import AnnouncementForm
from .models import Announcement


class AnnouncementAdminView(PermissionRequiredMixin, ListView):
    permission_required = ("announcements.change_announcement",)
    model = Announcement
    template_name = 'announcements/announcement_admin.html'
    context_object_name = "announcements"


class CreateAnnouncementView(PermissionRequiredMixin, CreateView):
    permission_required = ("announcements.add_announcement",)
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_create.html'
    success_url = reverse_lazy("announcement_admin")


class EditAnnouncementView(PermissionRequiredMixin, UpdateView):
    permission_required = ("announcements.change_announcement",)
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_edit.html'
    success_url = reverse_lazy("announcement_admin")


class DeleteAnnouncementView(PermissionRequiredMixin, DeleteView):
    permission_required = ("announcements.delete_announcement",)
    model = Announcement
    success_url = reverse_lazy("announcement_admin")
