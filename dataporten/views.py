from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.conf import settings


class Logout(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGOUT_URL)
