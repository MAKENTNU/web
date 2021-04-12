from django.urls import path

from . import views


urlpatterns = [
    path('', views.CommitteeList.as_view(), name='committee_list'),
    path('<int:pk>/', views.CommitteeDetailView.as_view(), name='committee_detail'),
    path('<int:pk>/edit', views.EditCommitteeView.as_view(), name='committee_edit'),
    path('admin/', views.CommitteeAdminView.as_view(), name='committee_admin'),
]
