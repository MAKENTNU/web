from math import ceil

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import ModelFormMixin

from util.templatetags.string_tags import title_en
from util.view_utils import (
    CustomFieldsetFormMixin,
    PreventGetRequestsMixin,
    QueryParameterFormMixin,
    insert_form_field_values,
)
from .forms import (
    AddPageForm,
    ChangePageVersionForm,
    DocumentationPageSearchQueryForm,
    PageContentForm,
)
from .models import Content, MAIN_PAGE_TITLE, Page


class DocumentationPageRelatedViewMixin:
    """
    NOTE: When extending this mixin class, it's required to have a ``PageTitle`` path converter named ``title`` as part of the view's path,
    which will be used to query the database for the requested page by title.
    """

    model = Page
    # The name of the model field that will be queried using the value of `slug_url_kwarg`
    slug_field = "title"
    # The name of the path parameter whose value will be used to query `slug_field`
    slug_url_kwarg = "title"
    # PKs will not be used to query objects
    pk_url_kwarg = None


class DocumentationPageDetailView(DocumentationPageRelatedViewMixin, DetailView):
    template_name = "docs/documentation_page_detail.html"
    context_object_name = "page"
    extra_context = {"MAIN_PAGE_TITLE": MAIN_PAGE_TITLE}

    is_main_page = False

    def get_object(self, *args, **kwargs):
        if self.is_main_page:
            return Page.get_main_page()
        return super().get_object(*args, **kwargs)


class DocumentationPageHistoryDetailView(DocumentationPageRelatedViewMixin, DetailView):
    template_name = "docs/documentation_page_history_detail.html"
    context_object_name = "page"


class DocumentationPageContentDetailView(DocumentationPageRelatedViewMixin, DetailView):
    template_name = "docs/documentation_page_detail.html"
    context_object_name = "page"
    extra_context = {"MAIN_PAGE_TITLE": MAIN_PAGE_TITLE}

    content: Content

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        content_pk = self.kwargs["content_pk"]
        self.content = get_object_or_404(
            self.get_object().content_history, pk=content_pk
        )

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "old": not hasattr(self.content, "page_currently_on"),
            "content": self.content,
            "last_edit_name": self.content.made_by.get_full_name()
            if self.content.made_by
            else _("Anonymous"),
            "form": ChangePageVersionForm(initial={"current_content": self.content}),
        }


class DocumentationPageVersionUpdateView(
    PermissionRequiredMixin,
    PreventGetRequestsMixin,
    DocumentationPageRelatedViewMixin,
    UpdateView,
):
    permission_required = ("docs.change_page",)
    form_class = ChangePageVersionForm

    def get_success_url(self):
        return self.get_object().get_absolute_url()

    def form_invalid(self, form):
        return HttpResponseForbidden()


class DocumentationPageCreateView(
    PermissionRequiredMixin, CustomFieldsetFormMixin, CreateView
):
    permission_required = ("docs.add_page",)
    model = Page
    form_class = AddPageForm

    base_template = "docs/base.html"
    narrow = False
    centered_title = False
    back_button_link = reverse_lazy("home")
    back_button_text = _("Documentation home page")
    save_button_text = _("Add")

    def get_form_kwargs(self):
        # Forcefully insert the user into the form
        return insert_form_field_values(
            super().get_form_kwargs(), {"created_by": self.request.user}
        )

    def get_form_title(self):
        return title_en(_("Add page"))

    def form_invalid(self, form):
        try:
            existing_page = Page.objects.get(title=form.data["title"])
        except Page.DoesNotExist:
            existing_page = None
        if existing_page:
            return HttpResponseRedirect(existing_page.get_absolute_url())
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("documentation_page_update", args=[self.object.pk])


class DocumentationPageUpdateView(
    PermissionRequiredMixin,
    CustomFieldsetFormMixin,
    DocumentationPageRelatedViewMixin,
    UpdateView,
):
    permission_required = ("docs.change_page",)
    form_class = PageContentForm
    template_name = "docs/documentation_page_form.html"

    base_template = "docs/base.html"
    narrow = False
    centered_title = False

    def get_initial(self):
        return {
            "content": self.object.current_content.content
            if self.object.current_content
            else "",
        }

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        # UpdateView inserts the Page instance into the Content form, so remove it, as a new Content instance will be created
        form_kwargs.pop("instance")
        # Forcefully insert the page and user into the form
        return insert_form_field_values(
            form_kwargs,
            {
                "page": self.object,
                "made_by": self.request.user,
            },
        )

    def get_form_title(self):
        return _("Change “{title}”").format(title=self.object)

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return _("View “{title}”").format(title=self.object)

    def form_valid(self, form):
        form.save()
        # ModelFormMixin sets `self.object = form.save()`, which we don't want,
        # as `get_success_url()` should still be able to refer to the Page object
        return super(ModelFormMixin, self).form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class DocumentationPageDeleteView(
    PermissionRequiredMixin,
    PreventGetRequestsMixin,
    DocumentationPageRelatedViewMixin,
    DeleteView,
):
    permission_required = ("docs.delete_page",)
    queryset = Page.objects.exclude(title=MAIN_PAGE_TITLE)
    success_url = reverse_lazy("home")


class DocumentationPageSearchView(QueryParameterFormMixin, TemplateView):
    form_class = DocumentationPageSearchQueryForm
    template_name = "docs/documentation_page_search.html"

    page_size = 10

    @staticmethod
    def pages_to_show(current_page, n_pages):
        if current_page <= 3:
            return range(1, min(n_pages + 1, 8))
        if current_page >= n_pages - 3:
            return range(max(1, n_pages - 6), n_pages + 1)
        return range(current_page - 3, current_page + 4)

    def get_context_data(self, **kwargs):
        query = self.query_params["query"]
        page = self.query_params["page"] or 1

        pages = Page.objects.filter(
            Q(title__icontains=query) | Q(current_content__content__icontains=query)
        )
        n_pages = ceil(pages.count() / self.page_size)

        return {
            **super().get_context_data(**kwargs),
            "pages": pages[(page - 1) * self.page_size : page * self.page_size],
            "page": page,
            "pages_to_show": self.pages_to_show(page, n_pages),
            "query": query,
        }
