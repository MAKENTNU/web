from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from users.models import User
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import CategoryForm, QuestionForm
from .models import Category, Question


class FAQListView(ListView):
    queryset = (
        Category.objects.prefetch_questions_and_default_order_by(
            questions_attr_name='existing_questions',
        ).filter(questions__isnull=False).distinct()  # Remove duplicates that can appear when filtering on values across tables
    )
    template_name = 'faq/faq_list.html'
    context_object_name = 'categories'


class FAQAdminPanelView(PermissionRequiredMixin, TemplateView):
    template_name = 'faq/faq_admin_panel.html'

    def has_permission(self):
        user: User = self.request.user
        return user.has_any_permissions_for(Category) or user.has_any_permissions_for(Question)


class AdminQuestionListView(PermissionRequiredMixin, ListView):
    model = Question
    queryset = Question.objects.order_by('title')
    template_name = 'faq/admin_question_list.html'
    context_object_name = 'questions'

    def has_permission(self):
        return self.request.user.has_any_permissions_for(Question)


class AdminCategoryListView(PermissionRequiredMixin, ListView):
    model = Category
    queryset = Category.objects.order_by('name')
    template_name = 'faq/admin_category_list.html'
    context_object_name = 'categories'

    def has_permission(self):
        return self.request.user.has_any_permissions_for(Category)


class QuestionFormMixin(CustomFieldsetFormMixin, ABC):
    model = Question
    form_class = QuestionForm
    success_url = reverse_lazy('admin_question_list')

    back_button_link = success_url
    back_button_text = _("Admin page for questions")


class QuestionCreateView(PermissionRequiredMixin, QuestionFormMixin, CreateView):
    permission_required = ('faq.add_question',)

    form_title = _("New Question")


class QuestionUpdateView(PermissionRequiredMixin, QuestionFormMixin, UpdateView):
    permission_required = ('faq.change_question',)

    form_title = _("Edit Question")


class QuestionDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('faq.delete_question',)
    model = Question
    success_url = reverse_lazy('admin_question_list')


class CategoryFormMixin(CustomFieldsetFormMixin, ABC):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('admin_category_list')

    back_button_link = success_url
    back_button_text = _("Admin page for categories")


class CategoryCreateView(PermissionRequiredMixin, CategoryFormMixin, CreateView):
    permission_required = ('faq.add_category',)

    form_title = _("New Category")


class CategoryUpdateView(PermissionRequiredMixin, CategoryFormMixin, UpdateView):
    permission_required = ('faq.change_category',)

    form_title = _("Edit Category")


class CategoryDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('faq.delete_category',)
    model = Category
    success_url = reverse_lazy('admin_category_list')
