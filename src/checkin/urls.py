from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


urlpatterns = [
    path("", views.UserSkillListView.as_view(), name='skills_present_list'),
    path("profile/", login_required(views.ProfileDetailView.as_view()), name='profile'),
    path("profile/edit/image/", login_required(views.AdminProfilePictureUpdateView.as_view()), name='profile_picture'),
    path("post/", views.AdminCheckInView.as_view()),
    path("register/card/", views.AdminRegisterCardView.as_view()),
    path("register/profile/", login_required(views.AdminAPIRegisterProfileView.as_view()), name='register_profile'),
    path("suggest/", login_required(views.AdminSuggestSkillView.as_view()), name='suggest_skill'),
    path("suggest/vote/", login_required(views.AdminAPISuggestSkillVoteView.as_view()), name='vote_for_skill_suggestion'),
    path("suggest/<int:pk>/delete/", login_required(views.AdminAPISuggestSkillDeleteView.as_view()), name='delete_skill_suggestion'),
]
