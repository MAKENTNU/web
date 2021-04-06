from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, UpdateView

from util.view_utils import CustomFieldsetFormMixin
from .forms import CommitteeForm
from .models import Committee


class CommitteeList(ListView):
    model = Committee
    template_name = 'groups/committee_list.html'
    context_object_name = 'committees'


class CommitteeDetailView(DetailView):
    model = Committee
    template_name = 'groups/committee_detail.html'
    context_object_name = 'committee'


class EditCommitteeView(PermissionRequiredMixin, CustomFieldsetFormMixin, UpdateView):
    permission_required = ('groups.change_committee',)
    model = Committee
    form_class = CommitteeForm
    success_url = reverse_lazy('committee_list')

    back_button_link = success_url
    back_button_text = _("Admin page for committees")

    def get_form_title(self):
        return _("Edit {committee}").format(committee=self.object)


class CommitteeAdminView(PermissionRequiredMixin, ListView):
    permission_required = ('groups.change_committee',)
    model = Committee
    template_name = 'groups/committee_admin.html'
    context_object_name = 'committees'
