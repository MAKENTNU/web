from django.urls import include, path

from . import views


urlpatterns = [
    path("", views.FAQListView.as_view(), name="faq_list"),
]

# --- Admin URL patterns (imported in `web/urls.py`) ---

specific_question_adminpatterns = [
    path("change/", views.QuestionUpdateView.as_view(), name="question_update"),
    path("delete/", views.QuestionDeleteView.as_view(), name="question_delete"),
]
question_adminpatterns = [
    path("", views.AdminQuestionListView.as_view(), name="admin_question_list"),
    path("add/", views.QuestionCreateView.as_view(), name="question_create"),
    path("<int:pk>/", include(specific_question_adminpatterns)),
]

specific_category_adminpatterns = [
    path("change/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
]
category_adminpatterns = [
    path("", views.AdminCategoryListView.as_view(), name="admin_category_list"),
    path("add/", views.CategoryCreateView.as_view(), name="category_create"),
    path("<int:pk>/", include(specific_category_adminpatterns)),
]

adminpatterns = [
    path("", views.AdminFAQPanelView.as_view(), name="admin_faq_panel"),
    path("questions/", include(question_adminpatterns)),
    path("categories/", include(category_adminpatterns)),
]
