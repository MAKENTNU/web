from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

urlpatterns = [
    path('', views.FAQPageView.as_view(), name='faq'),
    path('admin/', login_required(views.FAQAdminPanelView.as_view()), name='faq-admin'),
    path('admin/question/list', login_required(views.QuestionAdminView.as_view()), name='faq-question-list'),
    path('admin/question/create/', login_required(views.CreateQuestionView.as_view()), name='faq-question-create'),
    path('admin/<int:pk>/question/edit/', login_required(views.EditQuestionView.as_view()), name='faq-question-edit'),
    path('admin/<int:pk>/question/delete/', login_required(views.DeleteQuestionView.as_view()),
         name='faq-question-delete'),
    path('admin/category/list', login_required(views.CategoryAdminView.as_view()), name='faq-category-list'),
    path('admin/category/create/', login_required(views.CreateCategoryView.as_view()), name='faq-category-create'),
    path('admin/<int:pk>/category/edit/', login_required(views.EditCategoryView.as_view()), name='faq-category-edit'),
    path('admin/<int:pk>/category/delete/', login_required(views.DeleteCategoryView.as_view()),
         name='faq-category-delete'),
]
