from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView

from .models import Committee


class CommitteeList(ListView):
    model = Committee
    template_name = 'groups/committee_list.html'
    context_object_name = 'committees'


class EditCommitteeView(UpdateView):
    model = Committee
    fields = ('description', 'email', 'image')
    success_url = reverse_lazy('committee_list')
