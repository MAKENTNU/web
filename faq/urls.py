from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


urlpatterns = [
    path('', views.FAQListView.as_view(), name='faq_list'),
    path('admin/', login_required(views.FAQAdminListView.as_view()), name='faq_admin_list'),
    path('admin/create/', login_required(views.FAQCreateView.as_view()), name='faq_create'),
    path('admin/<int:pk>/edit/', login_required(views.FAQEditView.as_view()), name='faq_edit'),
    path('admin/<int:pk>/delete/', login_required(views.FAQDeleteView.as_view()), name='faq_delete'),
]
