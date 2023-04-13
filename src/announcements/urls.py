from django.urls import path

from . import views


urlpatterns = [
    path("admin/", views.AdminAnnouncementListView.as_view(), name='admin_announcement_list'),
    path("add/", views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path("<int:pk>/change/", views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path("<int:pk>/delete/", views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
]
