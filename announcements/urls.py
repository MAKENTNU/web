from django.urls import path

from announcements.views import AnnouncementAdminView

urlpatterns = [
    path('admin/', AnnouncementAdminView.as_view(), name="announcement_admin"),
]
