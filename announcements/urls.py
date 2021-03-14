from django.urls import path

from announcements.views import AnnouncementAdminView, CreateAnnouncementView, EditAnnouncementView, \
    DeleteAnnouncementView


urlpatterns = [
    path('admin/', AnnouncementAdminView.as_view(), name="announcement_admin"),
    path('create/', CreateAnnouncementView.as_view(), name="create_announcement"),
    path('<int:pk>/edit/', EditAnnouncementView.as_view(), name="edit_announcement"),
    path('<int:pk>/delete/', DeleteAnnouncementView.as_view(), name="delete_announcement"),
]
