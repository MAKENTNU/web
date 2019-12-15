from django.views.generic import DetailView

from docs.models import Page


class DocumentationPageView(DetailView):
    template_name = "docs/documentation_page.html"
    model = Page
    context_object_name = "page"
