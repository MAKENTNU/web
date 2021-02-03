from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('', views.FAQPageView.as_view(), name='faq'),
    path('admin/', login_required(views.FAQAdminView.as_view()), name='faq-admin'),
    path('admin/create/', login_required(views.CreateQuestionView.as_view()), name='faq-question-create'),
    path('admin/<int:pk>/edit/', login_required(views.EditQuestionView.as_view()), name='faq-question-edit'),
    path('admin/<int:pk>/delete/', login_required(views.DeleteQuestionView.as_view()), name='faq-question-delete'),
    path('admin/category/create/', login_required(views.CreateQuestionView.as_view()), name='faq-category-create'),
    path('admin/<int:pk>/category/edit/', login_required(views.EditQuestionView.as_view()), name='faq-category-edit'),
    path('admin/<int:pk>/category/delete/', login_required(views.DeleteQuestionView.as_view()),
         name='faq-category-delete'),
]
