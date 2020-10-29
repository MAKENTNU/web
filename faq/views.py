from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from contentbox.views import DisplayContentBoxView
from django.http import HttpResponse
from django.urls import reverse_lazy
# Create your views here.
from faq.forms import QuestionForm
from faq.models import Question, Category


class FAQPageView(ListView):
    template_name = 'faq/faqlist.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.prefetch_related('questions')


class CreateQuestionView(PermissionRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "faq/admin_question_create.html"
    context_object_name = 'question'
    permission_required = "can_add_question"
    success_url = reverse_lazy("FAQ-admin")


class FAQAdminView(PermissionRequiredMixin, ListView):
    model = Question
    template_name = "faq/faqadmin.html"
    context_object_name = "questionlist"
    permission_required = 'can_add_question'


class EditQuestionView(PermissionRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "faq/edit_question.html"
    context_object_name = 'question'
    permission_required = 'can_add_question'
    success_url = reverse_lazy("FAQ-admin")
