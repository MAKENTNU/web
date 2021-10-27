from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from util.templatetags.permission_tags import has_any_faq_permissions
from util.view_utils import PreventGetRequestsMixin
from .forms import QuestionForm
from .models import Category, Question


class FAQListView(ListView):
    queryset = Category.objects.prefetch_related('questions')
    template_name = 'faq/faq_list.html'
    context_object_name = 'categories'


class FAQAdminListView(PermissionRequiredMixin, ListView):
    model = Question
    template_name = 'faq/faq_admin.html'
    context_object_name = 'questions'

    def has_permission(self):
        return has_any_faq_permissions(self.request.user)


class FAQCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ('faq.add_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/question_create.html'
    context_object_name = 'question'
    success_url = reverse_lazy('faq_admin_list')


class FAQEditView(PermissionRequiredMixin, UpdateView):
    permission_required = ('faq.change_question',)
    model = Question
    form_class = QuestionForm
    template_name = 'faq/question_edit.html'
    context_object_name = 'question'
    success_url = reverse_lazy('faq_admin_list')


class FAQDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('faq.delete_question',)
    model = Question
    success_url = reverse_lazy('faq_admin_list')
