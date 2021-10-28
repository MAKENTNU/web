from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from util.templatetags.permission_tags import has_any_faq_permissions
from util.view_utils import PreventGetRequestsMixin
from .forms import CategoryForm, QuestionForm
from .models import Category, Question


class FAQListView(ListView):
    queryset = Category.objects.prefetch_related('questions')
    template_name = 'faq/faq_list.html'
    context_object_name = 'categories'


class FAQAdminPanelView(PermissionRequiredMixin, TemplateView):
    template_name = 'faq/faq_admin_panel.html'

    def has_permission(self):
        return has_any_faq_permissions(self.request.user)


class AdminQuestionListView(PermissionRequiredMixin, ListView):
    permission_required = ('faq.change_question',)
    model = Question
    queryset = Question.objects.order_by('title')
    template_name = 'faq/admin_question_list.html'
    context_object_name = 'questions'


class AdminCategoryListView(PermissionRequiredMixin, ListView):
    permission_required = ('faq.change_category',)
    model = Category
    queryset = Category.objects.order_by('name')
    template_name = 'faq/admin_category_list.html'
    context_object_name = 'categories'


class QuestionCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ('faq.add_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/admin_question_create.html'
    context_object_name = 'question'
    success_url = reverse_lazy('admin_question_list')


class QuestionUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = ('faq.change_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/admin_question_edit.html'
    context_object_name = 'question'
    success_url = reverse_lazy('admin_question_list')


class QuestionDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('faq.delete_question',)
    model = Question
    success_url = reverse_lazy('admin_question_list')


class CategoryCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ('faq.add_category',)
    model = Category
    form_class = CategoryForm
    template_name = 'faq/admin_category_create.html'
    context_object_name = 'category'
    success_url = reverse_lazy('admin_category_list')


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = ('faq.change_category',)
    model = Category
    form_class = CategoryForm
    template_name = 'faq/admin_category_edit.html'
    context_object_name = 'category'
    success_url = reverse_lazy('admin_category_list')


class CategoryDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('faq.delete_category',)
    model = Category
    success_url = reverse_lazy('admin_category_list')
