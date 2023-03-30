from ckeditor_uploader import views as ckeditor_views
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django_hosts import reverse


def reverse_internal(viewname: str, *args):
    return reverse(viewname, args=args, host='internal', host_args=['i'])


# Code based on https://github.com/django/django/blob/9c19aff7c7561e3a82978a272ecdaad40dda5c00/django/contrib/auth/decorators.py#L60-L82
def permission_required_else_denied(perm, login_url=None):
    """
    Decorator for views that checks whether a user has a particular permission.
    When the user does not have the permission, they will be redirected to the login page if not logged in,
    and a ``PermissionDenied`` will be raised if already logged in.
    """
    from users.models import User  # Avoids circular importing

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


def logout_urls():
    """
    Should be used in every URL config referenced in ``web/hosts.py``, so that the user can log out from each of the corresponding subdomains.

    DEV: It should technically be possible to only have one logout URL on e.g. the main subdomain, but when submitting the logout form on other
    subdomains (i.e. pressing the "Log out" button), multiple browsers (like Chrome) send an ``Origin`` header with a value of ``null``, which causes
    the CSRF verification to always fail.
    """
    from dataporten import views as dataporten_views  # Avoids circular importing

    # Both of these views log the user out, then redirects to the value of the `LOGOUT_REDIRECT_URL` setting
    if settings.USES_DATAPORTEN_AUTH:
        logout_view = dataporten_views.Logout.as_view()
    else:
        logout_view = auth_views.LogoutView.as_view()

    return i18n_patterns(
        # This path's `name` should be the same as the one for Django admin's logout URL
        # (https://github.com/django/django/blob/4.1.7/django/contrib/admin/sites.py#L270),
        # so that this path can override it, and consequently be used as intended in `admin_urls.py`
        path("logout/", logout_view, name='logout'),

        prefix_default_language=False,
    )


def ckeditor_uploader_urls():
    """
    Should be used in every URL config referenced in ``web/hosts.py``, so that the CKEditor uploader widgets work correctly.

    NOTE: The paths returned by this function must be used as top-level paths, with no prefix between the URL host and these paths
    (i.e. for example ``makentnu.no/<these paths>``).
    This is so that the CKEditor uploader widgets can reverse these paths regardless of the subdomain.
    """
    return [
        # Based on https://github.com/django-ckeditor/django-ckeditor/blob/9866ebe098794eca7a5132d6f2a4b1d1d837e735/ckeditor_uploader/urls.py#L8-L13
        path("ckeditor/upload/", permission_required_else_denied('contentbox.can_upload_image')(ckeditor_views.upload),
             name='ckeditor_upload'),
        path("ckeditor/browse/", never_cache(permission_required_else_denied('contentbox.can_browse_image')(ckeditor_views.browse)),
             name='ckeditor_browse'),
    ]


def debug_toolbar_urls():
    if not settings.USE_DEBUG_TOOLBAR:
        return []
    return [
        path("__debug__/", include('debug_toolbar.urls')),
    ]
