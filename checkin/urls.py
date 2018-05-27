from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from checkin.views import CheckInView, ShowSkillsView, ProfilePageView, SuggestSkillView, RegisterProfileView, \
    VoteSuggestionView, RegisterCardView, EditProfilePictureView

urlpatterns = [
    url(r'^$', ShowSkillsView.as_view()),
    url(r'^profile/$', login_required(ProfilePageView.as_view()), name="profile"),
    url(r'^profile/edit/image$', login_required(EditProfilePictureView.as_view()), name="profile_picture"),
    url(r'^post/$', CheckInView.as_view()),
    url(r'^register/card/$', RegisterCardView.as_view()),
    url(r'^register/profile/$', login_required(RegisterProfileView.as_view()), name="register_profile"),
    url(r'^suggest/$', login_required(SuggestSkillView.as_view()), name="suggest"),
    url(r'^suggest/vote/$', login_required(VoteSuggestionView.as_view()), name="vote"),
]
