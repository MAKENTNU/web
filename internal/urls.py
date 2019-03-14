from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.decorators import permission_required
from django.urls import path, include
from django_hosts import reverse

from internal.views import Home, MembersListView, AddMemberView, EditMemberView
from web.url_util import decorated_includes

unsafe_urlpatterns = [
    path("members", MembersListView.as_view(), name="members"),
    path("members/add", AddMemberView.as_view(), name="add-member"),
    path("members/<int:pk>/edit", EditMemberView.as_view(), name="edit-member"),
    path("", Home.as_view(), name="home"),
]

urlpatterns = [
    path("i18n/", decorated_includes(
        permission_required("internal.is_internal", login_url=reverse("login", host="main")),
        include("django.conf.urls.i18n")
    )),
]

urlpatterns += i18n_patterns(
    path("", decorated_includes(
        permission_required("internal.is_internal", login_url=reverse("login", host="main")),
        include(unsafe_urlpatterns)
    )),
    prefix_default_language=False
)
