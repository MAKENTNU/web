from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from .forms import QuestionForm, CategoryForm
from .models import Question, Category
from util.templatetags.permission_tags import has_any_faq_permissions


class FAQPageView(ListView):
    template_name = 'faq/faq_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.prefetch_related('questions')


class FAQAdminPanelView(PermissionRequiredMixin, TemplateView):
    template_name = 'faq/faq_admin_panel.html'

    def has_permission(self):
        return has_any_faq_permissions(self.request.user)


class QuestionAdminView(PermissionRequiredMixin, ListView):
    permission_required = ('faq.edit_question',)
    model = Question
    template_name = 'faq/admin_question_list.html'
    context_object_name = 'questions'
    queryset = Question.objects.order_by('title')


class CategoryAdminView(PermissionRequiredMixin, ListView):
    permission_required = ('faq.edit_category',)
    model = Category
    template_name = 'faq/admin_category_list.html'
    context_object_name = 'categories'
    queryset = Category.objects.order_by('name')


class CreateQuestionView(PermissionRequiredMixin, CreateView):
    permission_required = ('faq.create_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/admin_question_create.html'
    context_object_name = 'question'
    success_url = reverse_lazy('faq-question-list')


class EditQuestionView(PermissionRequiredMixin, UpdateView):
    permission_required = ('faq.edit_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/admin_question_edit.html'
    context_object_name = 'question'
    success_url = reverse_lazy('faq-question-list')


class DeleteQuestionView(PermissionRequiredMixin, DeleteView):
    permission_required = ('faq.delete_question',)
    model = Question
    success_url = reverse_lazy('faq-question-list')


class CreateCategoryView(PermissionRequiredMixin, CreateView):
    permission_required = ('faq.create_category',)
    model = Category
    form_class = CategoryForm
    template_name = 'faq/admin_category_create.html'
    context_object_name = 'category'
    success_url = reverse_lazy('faq-category-list')


class EditCategoryView(PermissionRequiredMixin, UpdateView):
    permission_required = ('faq.edit_category',)
    model = Category
    form_class = CategoryForm
    template_name = 'faq/admin_category_edit.html'
    context_object_name = 'category'
    success_url = reverse_lazy('faq-category-list')


class DeleteCategoryView(PermissionRequiredMixin, DeleteView):
    permission_required = ('faq.delete_category',)
    model = Category
    success_url = reverse_lazy('faq-category-list')
