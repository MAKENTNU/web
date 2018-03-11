from django.contrib.auth.models import User
from django.shortcuts import render
from django.views import View


class QuotaView(View):
    template_name = "make_queue/quota_panel.html"

    def get(self, request):
        return render(request, self.template_name, {"users": User.objects.all(), "user": request.user})
