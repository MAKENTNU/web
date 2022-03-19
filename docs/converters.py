from util.url_utils import SpecificObjectConverter
from .models import Content, Page
from .validators import page_title_regex


class SpecificPageByTitle:
    regex = page_title_regex.strip(r"^$")

    def to_python(self, value):
        try:
            return Page.objects.get(title=value).pk
        except Page.DoesNotExist:
            raise ValueError("No page exists with that title")

    def to_url(self, page: Page):
        return page.title


class SpecificContent(SpecificObjectConverter):
    model = Content
