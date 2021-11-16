from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views


urlpatterns = [
    path("", views.FAQListView.as_view(), name='faq_list'),
    path("admin/", login_required(views.FAQAdminPanelView.as_view()), name='faq_admin_panel'),
    path("admin/questions/", login_required(views.AdminQuestionListView.as_view()), name='admin_question_list'),
    path("admin/questions/add/", login_required(views.QuestionCreateView.as_view()), name='question_create'),
    path("admin/questions/<int:pk>/change/", login_required(views.QuestionUpdateView.as_view()), name='question_update'),
    path("admin/questions/<int:pk>/delete/", login_required(views.QuestionDeleteView.as_view()), name='question_delete'),
    path("admin/categories/", login_required(views.AdminCategoryListView.as_view()), name='admin_category_list'),
    path("admin/categories/add/", login_required(views.CategoryCreateView.as_view()), name='category_create'),
    path("admin/categories/<int:pk>/change/", login_required(views.CategoryUpdateView.as_view()), name='category_update'),
    path("admin/categories/<int:pk>/delete/", login_required(views.CategoryDeleteView.as_view()), name='category_delete'),
]
