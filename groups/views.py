from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from .models import Committee


class CommitteeList(ListView):
    model = Committee
    template_name = 'groups/committee_list.html'
    context_object_name = 'committees'


class CommitteeDetailView(DetailView):
    model = Committee
    context_object_name = 'committee'


class EditCommitteeView(PermissionRequiredMixin, UpdateView):
    permission_required = ('groups.change_committee',)
    model = Committee
    fields = ('clickbait', 'description', 'email', 'image')
    success_url = reverse_lazy('committee_list')


class CommitteeAdminView(PermissionRequiredMixin, ListView):
    permission_required = ('groups.change_committee',)
    model = Committee
    template_name = 'groups/committee_admin.html'
    context_object_name = 'committees'
