from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from util.templatetags.permission_tags import has_any_faq_permissions
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
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


class QuestionEditMixin(CustomFieldsetFormMixin, ABC):
    model = Question
    form_class = QuestionForm
    success_url = reverse_lazy('faq_admin_list')

    back_button_link = success_url
    back_button_text = _("Admin page for questions")


class FAQCreateView(PermissionRequiredMixin, QuestionEditMixin, CreateView):
    permission_required = ('faq.add_question',)

    form_title = _("New Question")


class FAQEditView(PermissionRequiredMixin, QuestionEditMixin, UpdateView):
    permission_required = ('faq.change_question',)

    form_title = _("Edit Question")


class FAQDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('faq.delete_question',)
    model = Question
    success_url = reverse_lazy('faq_admin_list')
