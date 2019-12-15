from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.datetime_safe import datetime
from django.views.generic import DetailView, FormView

from docs.forms import PageContentForm
from docs.models import Page, Content


class DocumentationPageView(DetailView):
    template_name = "docs/documentation_page.html"
    model = Page
    context_object_name = "page"


class EditDocumentationPageView(PermissionRequiredMixin, FormView):
    template_name = "docs/edit_documentation_page.html"
    model = Content
    form_class = PageContentForm
    permission_required = ()

    def get_page(self):
        return Page.objects.get(pk=self.kwargs.get("pk"))

    def get_initial(self):
        page = self.get_page()
        return {
            "content": page.content.content if page.content else ""
        }

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "page_title": self.get_page(),
        })
        return context_data

    def get_success_url(self):
        return reverse("page", kwargs={"pk": self.get_page()})

    def form_valid(self, form):
        redirect = super().form_valid(form)
        Content.objects.create(
            content=form.cleaned_data["content"],
            page=self.get_page(),
            changed=datetime.now(),
        )
        return redirect
