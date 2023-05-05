from django.urls import path

from . import views


urlpatterns = [
    path("admin/", views.AdminAnnouncementListView.as_view(), name='admin_announcement_list'),
    path("create/", views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path("<int:pk>/edit/", views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path("<int:pk>/delete/", views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
]
