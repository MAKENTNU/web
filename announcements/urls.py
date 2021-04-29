from django.urls import path

from . import views


urlpatterns = [
    path('admin/', views.AnnouncementAdminView.as_view(), name="announcement_admin"),
    path('create/', views.CreateAnnouncementView.as_view(), name="create_announcement"),
    path('<int:pk>/edit/', views.EditAnnouncementView.as_view(), name="edit_announcement"),
    path('<int:pk>/delete/', views.DeleteAnnouncementView.as_view(), name="delete_announcement"),
]
