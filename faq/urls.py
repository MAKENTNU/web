from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


urlpatterns = [
    path('', views.FAQPageView.as_view(), name='faq'),
    path('admin/', login_required(views.FAQAdminView.as_view()), name='faq-admin'),
    path('admin/create/', login_required(views.CreateQuestionView.as_view()), name='faq-create'),
    path('admin/<int:pk>/edit/', login_required(views.EditQuestionView.as_view()), name='faq-edit'),
    path('admin/<int:pk>/delete/', login_required(views.DeleteQuestionView.as_view()), name='faq-question-delete'),
]
