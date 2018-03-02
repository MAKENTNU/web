from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.conf import settings
from social_django.views import complete


class Logout(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGOUT_URL)


def login_wrapper(request, backend, *args, **kwargs):
    response = complete(request, backend, *args, **kwargs)
    user = request.user
    if not user.first_name:
        try:
            data = user.social_auth.first().extra_data
            user.first_name = ' '.join(data['fullname'].split()[:-1])
            user.last_name = data['fullname'].split()[-1]
            user.username = user.email.split('@')[0]
            user.save()
        except:
            pass
    return response
