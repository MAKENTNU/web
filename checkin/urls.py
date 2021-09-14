from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


urlpatterns = [
    path('', views.ShowSkillsView.as_view()),
    path('profile/', login_required(views.ProfilePageView.as_view()), name="profile"),
    path('profile/edit/image/', login_required(views.EditProfilePictureView.as_view()), name="profile_picture"),
    path('post/', views.CheckInView.as_view()),
    path('register/card/', views.RegisterCardView.as_view()),
    path('register/profile/', login_required(views.RegisterProfileView.as_view()), name="register_profile"),
    path('suggest/', login_required(views.SuggestSkillView.as_view()), name="suggest"),
    path('suggest/vote/', login_required(views.VoteSuggestionView.as_view()), name="vote"),
    path('suggest/delete/', login_required(views.DeleteSuggestionView.as_view()), name="delete"),
]
