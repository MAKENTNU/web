from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView

from internal.forms import AddMemberForm
from internal.models import Member


class Home(TemplateView):
    template_name = "internal/home.html"


class MembersListView(ListView):
    template_name = "internal/members.html"
    model = Member


class AddMemberView(PermissionRequiredMixin, CreateView):
    template_name = "internal/add_member.html"
    model = Member
    form_class = AddMemberForm
    permission_required = (
        "internal.can_register_new_member",
    )
    # TODO: Redirect to the member edit page for the new member
    success_url = reverse_lazy("members")
