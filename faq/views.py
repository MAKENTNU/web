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


class QuestionAdminView(PermissionRequiredMixin, ListView):
    permission_required = ('faq.change_question',)
    model = Question
    template_name = 'faq/admin_question_list.html'
    context_object_name = 'questions'
    queryset = Question.objects.order_by('title')


class CategoryAdminView(PermissionRequiredMixin, ListView):
    permission_required = ('faq.change_category',)
    model = Category
    template_name = 'faq/admin_category_list.html'
    context_object_name = 'categories'
    queryset = Category.objects.order_by('name')


class FAQCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ('faq.add_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/admin_question_create.html'
    context_object_name = 'question'
    success_url = reverse_lazy('faq-question-list')


class FAQEditView(PermissionRequiredMixin, UpdateView):
    permission_required = ('faq.change_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/admin_question_edit.html'
    context_object_name = 'question'
    success_url = reverse_lazy('faq-question-list')


class FAQDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('faq.delete_question',)
    model = Question
    success_url = reverse_lazy('faq-question-list')


class CreateCategoryView(PermissionRequiredMixin, CreateView):
    permission_required = ('faq.add_category',)
    model = Category
    form_class = CategoryForm
    template_name = 'faq/admin_category_create.html'
    context_object_name = 'category'
    success_url = reverse_lazy('faq-category-list')


class EditCategoryView(PermissionRequiredMixin, UpdateView):
    permission_required = ('faq.change_category',)
    model = Category
    form_class = CategoryForm
    template_name = 'faq/admin_category_edit.html'
    context_object_name = 'category'
    success_url = reverse_lazy('faq-category-list')


class DeleteCategoryView(PermissionRequiredMixin, DeleteView):
    permission_required = ('faq.delete_category',)
    model = Category
    success_url = reverse_lazy('faq-category-list')
