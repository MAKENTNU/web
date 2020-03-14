from django.urls import path

from announcements.views import AnnouncementAdminView, CreateAnnouncementView, EditAnnouncementView

urlpatterns = [
    path('admin/', AnnouncementAdminView.as_view(), name="announcement_admin"),
    path('create/', CreateAnnouncementView.as_view(), name="create_announcement"),
    path('<int:pk>/edit/', EditAnnouncementView.as_view(), name="edit_announcement"),
]
