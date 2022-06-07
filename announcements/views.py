from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import AnnouncementForm
from .models import Announcement


class AnnouncementAdminView(PermissionRequiredMixin, ListView):
    permission_required = ('announcements.change_announcement',)
    model = Announcement
    queryset = Announcement.objects.order_by('-display_from')
    template_name = 'announcements/announcement_admin.html'
    context_object_name = "announcements"


class AnnouncementFormMixin(CustomFieldsetFormMixin, ABC):
    model = Announcement
    form_class = AnnouncementForm
    success_url = reverse_lazy('announcement_admin')

    narrow = False
    centered_title = False
    back_button_link = success_url
    back_button_text = _("Admin page for announcements")
    custom_fieldsets = [
        {'fields': ('classification', 'link'), 'layout_class': "ui two fields"},
        {'fields': ('display_from', 'display_to'), 'layout_class': "ui two fields"},
        {'fields': ('content', 'site_wide')},
    ]


class CreateAnnouncementView(PermissionRequiredMixin, AnnouncementFormMixin, CreateView):
    permission_required = ('announcements.add_announcement',)

    form_title = _("New Announcement")


class EditAnnouncementView(PermissionRequiredMixin, AnnouncementFormMixin, UpdateView):
    permission_required = ('announcements.change_announcement',)

    form_title = _("Edit Announcement")


class DeleteAnnouncementView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('announcements.delete_announcement',)
    model = Announcement
    success_url = reverse_lazy('announcement_admin')
