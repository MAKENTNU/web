from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
# Create your views here.
from .forms import QuestionForm
from .models import Question, Category
from web.templatetags.permission_tags import has_any_faq_permissions


class FAQPageView(ListView):
    template_name = 'faq/faq_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.prefetch_related('questions')


class CreateQuestionView(PermissionRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "faq/question_create.html"
    context_object_name = 'question'
    success_url = reverse_lazy("FAQ-admin")

    def has_permission(self):
        return has_any_faq_permissions(self.request.user)


class FAQAdminView(PermissionRequiredMixin, ListView):
    model = Question
    template_name = "faq/faq_admin.html"
    context_object_name = "questionlist"

    def has_permission(self):
        return has_any_faq_permissions(self.request.user)


class EditQuestionView(PermissionRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "faq/question_edit.html"
    context_object_name = 'question'
    success_url = reverse_lazy("FAQ-admin")

    def has_permission(self):
        return has_any_faq_permissions(self.request.user)


class DeleteQuestionView(PermissionRequiredMixin, DeleteView):
    model = Question
    success_url = reverse_lazy('FAQ-admin')
    permission_required = 'faq.delete_question'

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
