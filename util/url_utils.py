from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import include, path
from django_hosts import reverse

from users.models import User


def reverse_internal(viewname: str, *args):
    return reverse(viewname, args=args, host='internal', host_args=['i'])


# Code based on https://github.com/django/django/blob/9c19aff7c7561e3a82978a272ecdaad40dda5c00/django/contrib/auth/decorators.py#L60-L82
def permission_required_else_denied(perm, login_url=None):
    """
    Decorator for views that checks whether a user has a particular permission.
    When the user does not have the permission, they will be redirected to the login page if not logged in,
    and a ``PermissionDenied`` will be raised if already logged in.
    """

    def check_perms(user: User):
        if not user.is_authenticated:
            # Will make `user_passes_test()` redirect the user to the login page
            return False

        if isinstance(perm, str):
            perms = (perm,)
        else:
            perms = perm
        if user.has_perms(perms):
            return True
        raise PermissionDenied

    return user_passes_test(check_perms, login_url=login_url)


def debug_toolbar_urls():
    if not settings.USE_DEBUG_TOOLBAR:
        return []
    return [
        path("__debug__/", include('debug_toolbar.urls')),
    ]
