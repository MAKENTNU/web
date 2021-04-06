from math import ceil

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView
from django.views.generic.edit import ModelFormMixin

from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin, insert_form_field_values
from .forms import ChangePageVersionForm, CreatePageForm, PageContentForm
from .models import MAIN_PAGE_TITLE, Page


class DocumentationPageDetailView(DetailView):
    model = Page
    template_name = 'docs/documentation_page_detail.html'
    context_object_name = "page"
    extra_context = {'MAIN_PAGE_TITLE': MAIN_PAGE_TITLE}


class HistoryDocumentationPageView(DetailView):
    model = Page
    template_name = 'docs/documentation_page_history.html'
    context_object_name = "page"


class OldDocumentationPageContentView(DetailView):
    model = Page
    template_name = 'docs/documentation_page_detail.html'
    context_object_name = "page"
    extra_context = {'MAIN_PAGE_TITLE': MAIN_PAGE_TITLE}

    def dispatch(self, request, *args, **kwargs):
        # A check to make sure that the given content is related to the given page. As to make sure that the database
        # stays in a correct state.
        if self.get_object() != self.get_content().page:
            return HttpResponseRedirect(reverse('page_detail', kwargs={'pk': self.get_object()}))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        return self.kwargs.get('content')

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        content = self.get_content()
        context_data.update({
            "old": True,
            "content": content,
            "last_edit_name": content.made_by.get_full_name() if content.made_by else _("Anonymous"),
            "form": ChangePageVersionForm(initial={"current_content": content}),
        })
        return context_data


class ChangeDocumentationPageVersionView(PermissionRequiredMixin, UpdateView):
    permission_required = ('docs.change_page',)
    model = Page
    form_class = ChangePageVersionForm

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('page_history', kwargs={'pk': self.get_object()}))

    def get_success_url(self):
        return reverse('page_detail', kwargs={'pk': self.get_object()})

    def form_invalid(self, form):
        return HttpResponseForbidden()


class CreateDocumentationPageView(PermissionRequiredMixin, CustomFieldsetFormMixin, CreateView):
    permission_required = ('docs.add_page',)
    model = Page
    form_class = CreatePageForm

    base_template = 'docs/base.html'
    form_title = _("Create a New Page")
    narrow = False
    centered_title = False
    back_button_link = reverse_lazy('home')
    back_button_text = _("Documentation home page")
    save_button_text = _("Add")

    def get_form_kwargs(self):
        # Forcefully insert the user into the form
        return insert_form_field_values(super().get_form_kwargs(), ('created_by', self.request.user))

    def form_invalid(self, form):
        try:
            existing_page = Page.objects.get(title=form.data["title"])
        except Page.DoesNotExist:
            existing_page = None
        if existing_page:
            return HttpResponseRedirect(reverse('page_detail', kwargs={'pk': existing_page}))
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('edit_page', kwargs={'pk': self.object})


class EditDocumentationPageView(PermissionRequiredMixin, CustomFieldsetFormMixin, UpdateView):
    permission_required = ('docs.change_page',)
    model = Page
    form_class = PageContentForm
    template_name = 'docs/documentation_page_edit.html'

    base_template = 'docs/base.html'
    narrow = False
    centered_title = False

    def get_initial(self):
        return {
            "content": self.object.current_content.content if self.object.current_content else "",
        }

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        # UpdateView inserts the Page instance into the Content form, so remove it, as a new Content instance will be created
        form_kwargs.pop('instance')
        # Forcefully insert the page and user into the form
        return insert_form_field_values(form_kwargs,
                                        ('page', self.object), ('made_by', self.request.user))

    def get_form_title(self):
        return _("Edit “{title}”").format(title=self.object)

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
        return reverse('page_detail', kwargs={'pk': self.object})


class DeleteDocumentationPageView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('docs.delete_page',)
    model = Page
    queryset = Page.objects.exclude(title=MAIN_PAGE_TITLE)
    success_url = reverse_lazy('home')


class SearchPagesView(TemplateView):
    template_name = 'docs/search.html'
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
