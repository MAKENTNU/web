from math import ceil

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.datetime_safe import datetime
from django.views.generic import DetailView, FormView, DeleteView, TemplateView, UpdateView

from docs.forms import PageContentForm, CreatePageForm, ChangePageVersionForm
from docs.models import Page, Content


class DocumentationPageView(DetailView):
    template_name = "docs/documentation_page.html"
    model = Page
    context_object_name = "page"


class HistoryDocumentationPageView(DetailView):
    template_name = "docs/documentation_page_history.html"
    model = Page
    context_object_name = "page"


class OldDocumentationPageContentView(DetailView):
    template_name = "docs/documentation_page.html"
    model = Page
    context_object_name = "page"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        content = self.kwargs.get("content")
        context_data.update({
            "old": True,
            "content": content,
            "form": ChangePageVersionForm(initial={"current_content": content})
        })
        return context_data


class ChangeDocumentationPageVersionView(PermissionRequiredMixin, UpdateView):
    model = Page
    form_class = ChangePageVersionForm
    permission_required = ("docs.change_page",)

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse("page-history", kwargs={"pk": self.get_object()}))

    def get_success_url(self):
        return reverse("page", kwargs={"pk": self.get_object()})


class CreateDocumentationPageView(PermissionRequiredMixin, FormView):
    template_name = "docs/create_documentation_page.html"
    model = Page
    form_class = CreatePageForm
    permission_required = ("docs.add_page",)

    def form_invalid(self, form):
        try:
            page = Page.objects.get(title=form.data["title"])
            return HttpResponseRedirect(reverse("page", kwargs={"pk": page}))
        except Page.DoesNotExist:
            return super().form_invalid(form)

    def form_valid(self, form):
        page = Page.objects.create(
            title=form.cleaned_data["title"],
            created_by=self.request.user,
        )
        return HttpResponseRedirect(reverse("edit-page", kwargs={"pk": page}))


class EditDocumentationPageView(PermissionRequiredMixin, FormView):
    template_name = "docs/edit_documentation_page.html"
    model = Content
    form_class = PageContentForm
    permission_required = ("docs.change_page",)

    def get_page(self):
        return Page.objects.get(pk=self.kwargs.get("pk"))

    def get_initial(self):
        page = self.get_page()
        return {
            "content": page.current_content.content if page.current_content else ""
        }

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "page": self.get_page(),
        })
        return context_data

    def get_success_url(self):
        return reverse("page", kwargs={"pk": self.get_page()})

    def form_valid(self, form):
        redirect = super().form_valid(form)
        page = self.get_page()
        if not page.current_content or form.cleaned_data["content"] != page.current_content.content:
            content = Content.objects.create(
                content=form.cleaned_data["content"],
                page=self.get_page(),
                changed=datetime.now(),
                made_by=self.request.user,
            )
            page.current_content = content
            page.save()
        return redirect


class DeleteDocumentationPageView(PermissionRequiredMixin, DeleteView):
    model = Page
    success_url = reverse_lazy("home")
    permission_required = ("docs.delete_page",)


class SearchPagesView(TemplateView):
    template_name = "docs/search.html"
    page_size = 10

    def pages_to_show(self, current_page, n_pages):
        if current_page <= 3:
            return range(1, min(n_pages + 1, 8))
        if current_page >= n_pages - 3:
            return range(max(1, n_pages - 6), n_pages + 1)
        return range(current_page - 3, current_page + 4)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        query = self.request.GET.get("query", "")
        page = int(self.request.GET.get("page", 1))
        pages = Page.objects.filter(Q(title__icontains=query) | Q(current_content__content__icontains=query))
        n_pages = ceil(pages.count() / self.page_size)
        context_data.update({
            "pages": pages[(page - 1) * self.page_size:page * self.page_size],
            "page": page,
            "pages_to_show": self.pages_to_show(page, n_pages),
            "query": query,
        })

        return context_data
