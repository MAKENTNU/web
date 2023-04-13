from django.urls import path

from . import views


urlpatterns = [
    path("admin/", views.AdminAnnouncementListView.as_view(), name='announcement_admin'),
    path("create/", views.AnnouncementCreateView.as_view(), name='create_announcement'),
    path("<int:pk>/edit/", views.AnnouncementUpdateView.as_view(), name='edit_announcement'),
    path("<int:pk>/delete/", views.AnnouncementDeleteView.as_view(), name='delete_announcement'),
]
