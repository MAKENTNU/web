from decorator_include import decorator_include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path
from django.views.generic import TemplateView
from django_hosts import reverse

from . import views


unsafe_urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("members", views.MembersListView.as_view(), name="members"),
    path("members/<int:pk>", views.MembersListView.as_view(), name="members"),
    path("members/add", views.AddMemberView.as_view(), name="add-member"),
    path("members/<int:pk>/edit", views.EditMemberView.as_view(), name="edit-member"),
    path("members/<int:pk>/quit", permission_required("internal.can_edit_group_membership")(views.MemberQuitView.as_view()), name="member-quit"),
    path("members/<int:pk>/quit/undo", permission_required("internal.can_edit_group_membership")(views.MemberUndoQuitView.as_view()),
         name="member-undo-quit"),
    path("members/<int:pk>/retire", permission_required("internal.can_edit_group_membership")(views.MemberRetireView.as_view()),
         name="member-retire"),
    path("members/<int:pk>/retire/undo", permission_required("internal.can_edit_group_membership")(views.MemberUndoRetireView.as_view()),
         name="member-undo-retire"),
    path("members/access/<int:pk>/change", views.ToggleSystemAccessView.as_view(), name="toggle-system-access"),
    path("secrets/", views.SecretsView.as_view(), name="secrets"),
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
