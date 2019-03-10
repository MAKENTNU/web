from django.views.generic import TemplateView, ListView

from internal.models import Member


class Home(TemplateView):
    template_name = "internal/home.html"


class MembersListView(ListView):
    template_name = "internal/members.html"
    model = Member
