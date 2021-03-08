from django.contrib.auth.decorators import login_required
from django.urls import path

from checkin.views import CheckInView, ShowSkillsView, ProfilePageView, SuggestSkillView, RegisterProfileView, \
    VoteSuggestionView, RegisterCardView, EditProfilePictureView, DeleteSuggestionView


urlpatterns = [
    path('', ShowSkillsView.as_view()),
    path('profile/', login_required(ProfilePageView.as_view()), name="profile"),
    path('profile/edit/image/', login_required(EditProfilePictureView.as_view()), name="profile_picture"),
    path('post/', CheckInView.as_view()),
    path('register/card/', RegisterCardView.as_view()),
    path('register/profile/', login_required(RegisterProfileView.as_view()), name="register_profile"),
    path('suggest/', login_required(SuggestSkillView.as_view()), name="suggest"),
    path('suggest/vote/', login_required(VoteSuggestionView.as_view()), name="vote"),
    path('suggest/delete/', login_required(DeleteSuggestionView.as_view()), name="delete"),
]
