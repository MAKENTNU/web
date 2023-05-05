from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


urlpatterns = [
    path("", views.UserSkillListView.as_view(), name='user_skill_list'),
    path("profile/", login_required(views.ProfileDetailView.as_view()), name='profile_detail'),
    path("profile/edit/image/", login_required(views.AdminProfilePictureUpdateView.as_view()), name='admin_profile_picture_update'),
    path("post/", views.AdminCheckInView.as_view()),
    path("register/card/", views.AdminRegisterCardView.as_view()),
    path("register/profile/", login_required(views.AdminAPIRegisterProfileView.as_view()), name='admin_api_register_profile'),
    path("suggest/", login_required(views.AdminSuggestSkillView.as_view()), name='admin_suggest_skill'),
    path("suggest/vote/", login_required(views.AdminAPISuggestSkillVoteView.as_view()), name='admin_api_suggest_skill_vote'),
    path("suggest/<int:pk>/delete/", login_required(views.AdminAPISuggestSkillDeleteView.as_view()), name='admin_api_suggest_skill_delete'),
]
