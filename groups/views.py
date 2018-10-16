from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DetailView

from .models import Committee


class CommitteeList(ListView):
    model = Committee
    template_name = 'groups/committee_list.html'
    context_object_name = 'committees'


class EditCommitteeView(UpdateView):
    model = Committee
    fields = ('clickbait', 'description', 'email', 'image')
    success_url = reverse_lazy('committee_list')


class CommitteeDetailView(DetailView):
    model = Committee
    context_object_name = 'committee'


class CommitteeAdminView(PermissionRequiredMixin, ListView):
    model = Committee
    context_object_name = 'committees'
    template_name = 'groups/committee_admin.html'
    permission_required = (
        'groups.change_committee',
    )
