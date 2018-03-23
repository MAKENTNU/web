from django.views.generic import ListView

from .models import Committee


class CommitteeList(ListView):
    template_name = 'groups/committee_list.html'
    context_object_name = 'committees'
    model = Committee
