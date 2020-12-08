from decorator_include import decorator_include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path
from django.views.generic import TemplateView
from django_hosts import reverse

from . import views


unsafe_urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("members/", views.MemberListView.as_view(), name='member_list'),
    path("members/<int:pk>/", views.MemberListView.as_view(), name='member_list'),
    path("members/create/", views.CreateMemberView.as_view(), name='create_member'),
    path("members/<int:pk>/edit/", views.EditMemberView.as_view(), name="edit-member"),
    path("members/<int:pk>/edit/status/", views.EditMemberStatusView.as_view(), name="edit-member-status"),
    path("members/<int:pk>/edit/status/quit/", views.MemberQuitView.as_view(), name="member-quit"),
    path("members/<int:member_pk>/access/<int:pk>/edit/", views.EditSystemAccessView.as_view(), name="edit-system-access"),
    path("secrets/", views.SecretListView.as_view(), name='secret_list'),
    path("secrets/<int:pk>/edit/", views.EditSecretView.as_view(), name="edit-secret"),
    path("secrets/create/", views.CreateSecretView.as_view(), name="create-secret"),
    path("secrets/<int:pk>/delete/", views.DeleteSecretView.as_view(), name="delete-secret")
]

LOGIN_URL = reverse('login', host='main')

urlpatterns = i18n_patterns(
    path("", decorator_include(
        permission_required('internal.is_internal', login_url=LOGIN_URL),
        unsafe_urlpatterns
    )),
    prefix_default_language=False,
)

urlpatterns += [
    path("robots.txt", TemplateView.as_view(template_name='internal/robots.txt', content_type='text/plain')),
    path("i18n/", decorator_include(
        permission_required('internal.is_internal', login_url=LOGIN_URL),
        'django.conf.urls.i18n'
    )),
]
