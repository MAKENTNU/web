from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.conf import settings
from social_django.views import complete
from .login_handlers import run_handlers


class Logout(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGOUT_URL)


def login_wrapper(request, backend, *args, **kwargs):
    response = complete(request, backend, *args, **kwargs)
    run_handlers(request.user)
    return response
