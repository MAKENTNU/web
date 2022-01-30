from decorator_include import decorator_include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import include, path
from django.views.generic import TemplateView
from django_hosts import reverse

from contentbox.views import EditContentBoxView
from . import views


internal_contentbox_urlpatterns = [
    path("<int:pk>/edit/",
         permission_required('contentbox.change_internal_contentbox', raise_exception=True)(EditContentBoxView.as_view(base_template='internal/base.html')),
         name='contentbox_edit'),
]

internal_urlpatterns = [
    path("", views.HomeView.as_view(), name='home'),
    path("contentbox/", include(internal_contentbox_urlpatterns)),
]

member_urlpatterns = [
    path("members/", views.MemberListView.as_view(), name='member_list'),
    path("members/<int:pk>/", views.MemberListView.as_view(), name='member_list'),
    path("members/create/", views.CreateMemberView.as_view(), name='create_member'),
    path("members/<int:pk>/edit/", views.EditMemberView.as_view(), name='edit_member'),
    path("members/<int:pk>/edit/status/", views.EditMemberStatusView.as_view(), name='edit_member_status'),
    path("members/<int:pk>/edit/status/quit/", views.MemberQuitView.as_view(), name='member_quit'),
    path("members/<int:pk>/edit/status/retire/", views.MemberRetireView.as_view(), name='member_retire'),
    path("members/<int:member_pk>/access/<int:pk>/edit/", views.EditSystemAccessView.as_view(), name='edit_system_access'),
]

secret_urlpatterns = [
    path("secrets/", views.SecretListView.as_view(), name='secret_list'),
    path("secrets/create/", views.CreateSecretView.as_view(), name='create_secret'),
    path("secrets/<int:pk>/edit/", views.EditSecretView.as_view(), name='edit_secret'),
    path("secrets/<int:pk>/delete/", views.DeleteSecretView.as_view(), name='delete_secret'),
]

LOGIN_URL = reverse('login', host='main')

urlpatterns = i18n_patterns(
    path("", decorator_include(
        permission_required('internal.is_internal', login_url=LOGIN_URL),
        internal_urlpatterns
    )),
    path("", decorator_include(
        permission_required('internal.view_member', login_url=LOGIN_URL),
        member_urlpatterns
    )),
    path("", decorator_include(
        permission_required('internal.view_secret', login_url=LOGIN_URL),
        secret_urlpatterns
    )),

    prefix_default_language=False,
)

urlpatterns += [
    path("robots.txt", TemplateView.as_view(template_name='internal/robots.txt', content_type='text/plain')),
    path(".well-known/security.txt", TemplateView.as_view(template_name='web/security.txt', content_type='text/plain')),
    path("i18n/", decorator_include(
        permission_required('internal.is_internal', login_url=LOGIN_URL),
        'django.conf.urls.i18n'
    )),
]
