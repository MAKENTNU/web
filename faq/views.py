from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from util.templatetags.permission_tags import has_any_faq_permissions
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import CategoryForm, QuestionForm
from .models import Category, Question


class FAQListView(ListView):
    queryset = (
        Category.objects.prefetch_questions_and_default_order_by(
            questions_attr_name='existing_questions',
        ).filter(questions__isnull=False).distinct()  # remove duplicates that can appear when filtering on values across tables
    )
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
