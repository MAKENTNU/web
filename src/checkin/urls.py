from django.contrib.auth.decorators import login_required
from django.urls import include, path

from . import views


urlpatterns = [
    path("", views.UserSkillListView.as_view(), name='user_skill_list'),
    path("profile/", login_required(views.ProfileDetailView.as_view()), name='profile_detail'),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

adminpatterns = [
    path("profile/change/image/", views.AdminProfilePictureUpdateView.as_view(), name='admin_profile_picture_update'),
    path("post/", views.AdminCheckInView.as_view(), name='admin_check_in'),
    path("register/card/", views.AdminRegisterCardView.as_view(), name='admin_register_card'),
    path("suggest/", views.AdminSuggestSkillView.as_view(), name='admin_suggest_skill'),
]

# --- Admin API URL patterns (imported in `web/urls.py`) ---

suggest_skill_adminapipatterns = [
    path("vote/", views.AdminAPISuggestSkillVoteView.as_view(), name='admin_api_suggest_skill_vote'),
    path("<int:pk>/delete/", views.AdminAPISuggestSkillDeleteView.as_view(), name='admin_api_suggest_skill_delete'),
]

adminapipatterns = [
    path("register/profile/", views.AdminAPIRegisterProfileView.as_view(), name='admin_api_register_profile'),
    path("suggest/", include(suggest_skill_adminapipatterns)),
]
