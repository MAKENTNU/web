from django.contrib.auth.views import LoginView
from django_hosts import reverse, reverse_host


def login(request):
    # The current `next` parameter
    current_redirect_url = LoginView(request=request).get_redirect_url()

    login_path = reverse('login', host="main").partition(reverse_host("main"))[-1]
    # If at the login page:
    if request.path.startswith(login_path.rstrip("/")):
        # Let the `next` parameter be the same as it currently is
        login_redirect_path = current_redirect_url
    # If at the front page:
    elif request.path == "/":
        # Omit the `next` parameter
        login_redirect_path = None
    else:
        # Redirect back to the same page after logging in
        login_redirect_path = request.path

    return {
        'login_next_param': f"?next={login_redirect_path}" if login_redirect_path else "",
    }
